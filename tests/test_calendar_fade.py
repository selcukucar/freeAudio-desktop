import ast
from pathlib import Path
import types
import unittest
from unittest.mock import Mock


class CalendarFadeTests(unittest.TestCase):
    def manager(self):
        path=Path(__file__).resolve().parents[1]/'vendor/freeAudio/timerManager.py'
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        methods=[node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef) and node.name in ('_fade_and_stop','_stop_player')]
        cls=ast.ClassDef(name='Timer',bases=[],keywords=[],body=methods,decorator_list=[])
        namespace={'wx':types.SimpleNamespace(CallAfter=lambda fn,*args:fn(*args)),
                   '_notify':Mock(),'_':lambda s:s}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[cls],type_ignores=[])),str(path),'exec'),namespace)
        timer=namespace['Timer']()
        player=timer._player=Mock()
        player.is_playing.return_value=True
        player.get_current_station.return_value={'url':'old'}
        player.get_volume.return_value=100
        player.set_volume.side_effect=lambda value:setattr(player.get_volume,'return_value',value)
        timer._stop_event=Mock();timer._stop_event.wait.return_value=False
        timer._desktop_stop=Mock();timer._desktop_generation=Mock(return_value=1)
        return timer,player

    def test_successful_fade_restores_volume_and_routes_stop_through_desktop_gate(self):
        timer,player=self.manager();timer._fade_and_stop()
        self.assertEqual(player.get_volume(),100)
        self.assertIn(0,[call.args[0] for call in player.set_volume.call_args_list])
        timer._desktop_stop.assert_called_once_with({'url':'old'},1)
        player.stop.assert_not_called()

    def test_new_media_volume_change_or_new_request_cancels_fade_without_overwrite(self):
        for change in ('media','volume','generation','termination'):
            with self.subTest(change=change):
                timer,player=self.manager()
                def tick(delay):
                    if change=='media':player.get_current_station.return_value={'url':'new'}
                    if change=='volume':player.get_volume.return_value=77
                    if change=='generation':timer._desktop_generation.return_value=2
                    return change=='termination'
                timer._stop_event.wait.side_effect=tick
                timer._fade_and_stop()
                timer._desktop_stop.assert_not_called();player.stop.assert_not_called()
                player.set_volume.assert_not_called()


if __name__=='__main__':unittest.main()
