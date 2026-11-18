from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from tools.signing import sign_file


class SigningTests(unittest.TestCase):
    def test_hook_is_followed_by_trust_and_timestamp_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            target, hook, tool = [Path(directory) / name for name in ('app.exe', 'hook.py', 'signtool.exe')]
            for path in (target, hook, tool):
                path.touch()
            with patch('tools.signing.subprocess.run') as run:
                sign_file(target, hook, tool)
            self.assertEqual(len(run.call_args_list), 2)
            self.assertEqual(run.call_args_list[0].args[0][-2:], [str(hook.resolve()), str(target.resolve())])
            self.assertEqual(run.call_args_list[1].args[0][1:], ['verify', '/pa', '/all', '/tw', '/v', str(target.resolve())])
            self.assertTrue(all(call.kwargs['check'] for call in run.call_args_list))

    def test_signing_failure_aborts_before_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            target, hook, tool = [Path(directory) / name for name in ('app.exe', 'hook.py', 'signtool.exe')]
            for path in (target, hook, tool):
                path.touch()
            with patch('tools.signing.subprocess.run', side_effect=subprocess.CalledProcessError(1, 'sign')) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    sign_file(target, hook, tool)
            run.assert_called_once()
