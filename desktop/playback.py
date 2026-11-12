"""Cancel queued playback without depending on a selected library row."""
import itertools
import threading


class PlaybackGate:
    def __init__(self):
        self._ids = itertools.count(1)
        self.current = 0
        self.pending = None
        self.lock = threading.RLock()

    def request(self):
        # Request/cancel never waits for audio IPC on the interface thread.
        self.current = next(self._ids)
        self.pending = self.current
        return self.current

    def cancel(self):
        token = self.request()
        self.pending = None
        return token

    def run(self, token, action):
        with self.lock:
            if token != self.current:
                return False
            try:
                action()
            finally:
                if self.pending == token:
                    self.pending = None
            return True


def install_playback_gate(plugin_class, gate):
    original_play = plugin_class._play_station
    original_start = plugin_class._start_playing
    original_resume = plugin_class._resume_last_station
    context = threading.local()

    def play(self, station, *args, **kwargs):
        token = getattr(context, 'resume_token', None)
        if token is not None:
            context.play_scheduled = True
        if token is not None and token != gate.current:
            return
        if token is None:
            token = gate.request()
        station = dict(station)
        station['_desktop_play_request'] = token
        def work():
            if token == gate.current and not getattr(self, '_recording_shutdown', False):
                original_play(self, station, *args, **kwargs)
        threading.Thread(target=work, daemon=True, name='desktop-play-request').start()

    def start(self, url, name, url_resolved='', station=None):
        station = dict(station or {})
        token = station.pop('_desktop_play_request', gate.current)
        if not getattr(self, '_recording_shutdown', False):
            gate.run(token, lambda: original_start(self, url, name, url_resolved, station))

    plugin_class._play_station = play
    plugin_class._start_playing = start

    def resume(self, startup=False):
        if startup and gate.current != 0:
            return
        token = gate.request()
        def work():
            context.resume_token = token
            context.play_scheduled = False
            try:
                if token == gate.current and not getattr(self, '_recording_shutdown', False):
                    original_resume(self)
            finally:
                if not context.play_scheduled and gate.pending == token:
                    gate.pending = None
                del context.resume_token
                del context.play_scheduled
        threading.Thread(target=work, daemon=True, name='desktop-resume-request').start()
    plugin_class._resume_last_station = resume
