"""Optional external signing hook; a valid Authenticode signature is mandatory."""
from pathlib import Path
import subprocess
import sys


def sign_file(target, hook, signtool):
    target, hook, signtool = Path(target).resolve(), Path(hook).resolve(), Path(signtool).resolve()
    if not all(path.is_file() for path in (target, hook, signtool)):
        raise FileNotFoundError('Signing target, hook and signtool must exist')
    # The hook receives only a file path. Signing credentials belong in the
    # provider's environment/secret store, never command arguments or the repo.
    subprocess.run([sys.executable, str(hook), str(target)], check=True)
    subprocess.run([str(signtool), 'verify', '/pa', '/all', '/tw', '/v', str(target)], check=True)
