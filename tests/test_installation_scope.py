import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from desktop.installation import installation_scope
from desktop.storage import data_directory
from desktop.updates import launch_installer


class InstallationScopeTests(unittest.TestCase):
    def test_legacy_installations_remain_per_user_for_bootstrap_updates(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(installation_scope(directory),'current')

    def test_installer_markers_support_both_scopes_and_windows_encodings(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'install-mode.ini'
            for scope in ('all','current'):
                for encoding in ('utf-8','utf-8-sig','utf-16'):
                    with self.subTest(scope=scope,encoding=encoding):
                        path.write_text('[Install]\nScope='+scope+'\n',encoding=encoding)
                        self.assertEqual(installation_scope(directory),scope)

    def test_invalid_marker_cannot_launch_an_installer(self):
        with tempfile.TemporaryDirectory() as directory:
            marker=Path(directory)/'install-mode.ini'
            for text in ('broken','[Install]\nScope=unknown','x'*17000):
                marker.write_text(text)
                with self.assertRaises(ValueError):installation_scope(directory)
                with patch('desktop.updates.verify_download',return_value=Path(directory)/'setup.exe'),patch(
                        'desktop.updates.subprocess.Popen') as launch,self.assertRaises(ValueError):
                    launch_installer(Mock(portable=False,version='1.2.1'),'setup.exe',directory)
                launch.assert_not_called()

    def test_updates_explicitly_keep_the_installed_scope_and_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            marker=Path(directory)/'install-mode.ini'
            for scope,option in (('all','/ALLUSERS'),('current','/CURRENTUSER')):
                marker.write_text('[Install]\nScope='+scope)
                with patch('desktop.updates.verify_download',return_value=Path(directory)/'setup.exe'),patch(
                        'desktop.updates.subprocess.Popen') as launch:
                    launch_installer(Mock(portable=False,version='1.2.1'),'setup.exe',directory)
                args=launch.call_args.args[0]
                self.assertIn(option,args)
                self.assertIn('/DIR='+str(Path(directory).resolve()),args)
                self.assertFalse(launch.call_args.kwargs['shell'])

    def test_installed_data_directory_does_not_depend_on_install_scope(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict('os.environ',{'APPDATA':directory}):
            for scope in ('all','current'):
                application=Path(directory)/scope
                application.mkdir()
                (application/'install-mode.ini').write_text('[Install]\nScope='+scope)
                self.assertEqual(data_directory(application),Path(directory)/'freeAudioDesktop')
