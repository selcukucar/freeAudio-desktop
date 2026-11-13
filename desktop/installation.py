"""Installer scope is separate from each user's unchanged Roaming profile."""
import configparser
from pathlib import Path


def installation_scope(app_directory):
    marker = Path(app_directory) / 'install-mode.ini'
    if not marker.exists():
        # Releases through 1.2.0 installed only for the current user.
        return 'current'
    raw = marker.read_bytes()
    if len(raw) > 16384:
        raise ValueError('Invalid installation scope marker')
    encoding = 'utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(raw.decode(encoding))
        scope = parser.get('Install', 'Scope', fallback='').strip().lower()
    except (UnicodeError, configparser.Error) as error:
        raise ValueError('Invalid installation scope marker') from error
    if scope not in ('all', 'current'):
        raise ValueError('Invalid installation scope marker')
    return scope
