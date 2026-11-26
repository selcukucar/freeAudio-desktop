"""Session-only sleep countdown; no operating-system actions in this model."""
import math
import time


def media_identity(station):
    if not station:
        return None
    if station.get('getem_detail_url'):
        return ('book', station['getem_detail_url'], station.get('getem_chapter_index', 0))
    return (station.get('media_kind', ''), station.get('podcast_resume_key') or station.get('url'))


class SleepTimer:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.cancel()

    def cancel(self):
        was_active = getattr(self, 'mode', None) is not None
        self.mode = self.action = self.deadline = self.target = None
        self.warned = False
        return was_active

    def arm(self, minutes=None, target=None, action='stop'):
        if action not in ('stop', 'shutdown'):
            raise ValueError('Invalid sleep action')
        if minutes is not None and (type(minutes) is not int or not 1 <= minutes <= 480):
            raise ValueError('Choose between 1 and 480 minutes.')
        if minutes is None and not target:
            raise ValueError('Play a podcast episode or audio book chapter first.')
        self.cancel()
        self.action, self.target = action, target
        self.mode = 'minutes' if minutes is not None else 'end'
        self.deadline = self.clock() + minutes * 60 if minutes is not None else None

    def remaining(self):
        return max(0, math.ceil(self.deadline - self.clock())) if self.deadline is not None else None

    def changed_media(self, identity):
        if self.mode == 'end' and identity is not None and identity != self.target:
            self.cancel()
            return True
        return False

    def finished(self, identity):
        if self.mode != 'end' or identity != self.target:
            return None
        if self.action == 'stop':
            self.cancel()
            return 'stop'
        self.mode, self.deadline, self.target = 'countdown', self.clock() + 60, None
        return 'countdown'

    def poll(self):
        remaining = self.remaining()
        if remaining is None:
            return None
        if self.action == 'shutdown' and remaining <= 60 and not self.warned:
            # A suspended or busy computer must still provide a full warning.
            self.deadline = max(self.deadline, self.clock() + 60)
            self.warned = True
            return 'warning'
        if remaining == 0:
            action = self.action
            self.cancel()
            return action
        return None


def request_windows_shutdown(test_mode=False):
    """Called only after the application's own cancellable countdown and checks."""
    import os
    from pathlib import Path
    import subprocess
    if test_mode:
        raise RuntimeError('Power actions are disabled in test mode.')
    executable = Path(os.environ['SystemRoot']) / 'System32' / 'shutdown.exe'
    # /t 0 avoids Windows' implicit force-close behaviour for nonzero /t.
    # Our application supplies the countdown; never add /f.
    subprocess.run([str(executable), '/s', '/t', '0'], check=True, timeout=15,
                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
