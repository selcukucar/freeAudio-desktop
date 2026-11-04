"""Versioned, atomic settings, with separate installed and portable locations."""
import json
import os
import ast
from functools import lru_cache
from pathlib import Path
from configobj.validate import Validator, ValidateError


@lru_cache(maxsize=1)
def setting_specs():
    """Read the engine's declared schema without importing or executing its host."""
    source = Path(__file__).resolve().parents[1] / 'vendor/freeAudio/__init__.py'
    for node in ast.walk(ast.parse(source.read_text(encoding='utf-8-sig'))):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            for target in node.targets:
                if (isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant)
                        and target.slice.value == 'freeAudio' and isinstance(target.value, ast.Attribute)
                        and target.value.attr == 'spec'):
                    return ast.literal_eval(node.value)
    raise ValueError('The application settings schema could not be loaded.')


def validate_settings(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get('settings', {}), dict):
        raise ValueError('Invalid settings file; your data has not been changed.')
    if type(raw.get('schema_version', 1)) is not int or raw.get('schema_version', 1) != 1:
        raise ValueError('Unsupported settings schema; your data has not been changed.')
    sections = raw.get('settings', {})
    if not all(isinstance(value, dict) for value in sections.values()):
        raise ValueError('Invalid settings sections; your data has not been changed.')
    validator = Validator()
    values = sections.get('freeAudio', {})
    for key, spec in setting_specs().items():
        if key in values:
            try:
                validator.check(spec, values[key])
            except ValidateError as error:
                raise ValueError('Invalid setting: ' + key) from error
    desktop = sections.get('desktop', {})
    if desktop.get('language', 'tr') not in ('tr', 'en'):
        raise ValueError('Unsupported application language.')
    shortcuts = desktop.get('shortcuts', {})
    if not isinstance(shortcuts, dict) or not all(isinstance(key, str) and isinstance(value, str)
                                                for key, value in shortcuts.items()):
        raise ValueError('Invalid shortcut settings.')
    from .updates import valid_repository
    repository = desktop.get('update_repository', '')
    if not isinstance(repository, str) or (repository and not valid_repository(repository)):
        raise ValueError('Invalid update repository in settings.')


def data_directory(app_dir, portable=False):
    app_dir = Path(app_dir)
    if portable or (app_dir / 'portable.flag').exists():
        return app_dir / 'data'
    return Path(os.environ.get('APPDATA', Path.home())) / 'freeAudioDesktop'


class Settings(dict):
    def __init__(self, directory):
        super().__init__()
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / 'settings.json'
        self.spec = {}
        self.profiles = [self]
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding='utf-8'))
            validate_settings(raw)
            self.update(raw.get('settings', {}))
            if not all(isinstance(value, dict) for value in self.values()):
                raise ValueError('Invalid settings sections; your data has not been changed.')
            # Preserve alpha.1 preferences while using independent-app terminology.
            if self.get('freeAudio', {}).get('track_change_voice') == 'nvda':
                self['freeAudio']['track_change_voice'] = 'screen_reader'

    def __getitem__(self, section):
        if section not in self:
            self[section] = {}
        values = super().__getitem__(section)
        validator = Validator()
        for key, spec in self.spec.get(section, {}).items():
            if key not in values:
                values[key] = validator.get_default_value(spec)
            else:
                values[key] = validator.check(spec, values[key])
        return values

    def save(self):
        payload = {'schema_version': 1, 'settings': dict(self)}
        validate_settings(payload)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps(payload,
                                         ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporary, self.path)
