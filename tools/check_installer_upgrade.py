"""Exercise per-user installer upgrades only on disposable GitHub Windows runners."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from desktop.updates import find_asset, download_update
from desktop.version import VERSION


def main():
    if os.environ.get('GITHUB_ACTIONS') != 'true' or not os.environ.get('RUNNER_TEMP'):
        raise SystemExit('This integration check only runs on disposable GitHub Actions runners.')
    root = Path(os.environ['RUNNER_TEMP']) / ('freeAudio-upgrade-' + VERSION)
    root.mkdir(exist_ok=True)
    app = root / 'application'
    profile = root / 'roaming/freeAudioDesktop'
    profile.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, APPDATA=str(profile.parent), FREEAUDIO_SKIP_AUDIO_DEVICE_TEST='1')
    old = download_update(find_asset('selcukucar/freeAudio-desktop', '1.1.1'), root / 'downloads')
    setup = ROOT / ('releases/freeAudio-Desktop-' + VERSION + '-win64-setup.exe')
    for installer in (old, setup):
        command = [str(installer), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOICONS',
                   '/DIR=' + str(app), '/LOG=' + str(root / (installer.name + '.log'))]
        subprocess.run(command, env=env, check=True, timeout=180)
        executable = app / 'freeAudioDesktop.exe'
        if installer == old:
            assert executable.is_file()
            (profile / 'settings.json').write_text(json.dumps({'schema_version': 1, 'settings': {
                'desktop': {'language': 'en', 'last_version': '1.1.1'},
                'freeAudio': {'legacy_migrated': True, 'volume': 37, 'resume_on_start': False,
                              'auto_check_updates': False}}}), encoding='utf-8')
            (profile / 'freeAudio_favorites.json').write_text('[{"name":"Upgrade fixture","stationuuid":"fixture"}]')
            (profile / 'podcast_positions.json').write_text('{"episode":{"position":42.5,"length":120}}')
    subprocess.run([str(executable), '--smoke-test'], env=env, check=True, timeout=90)
    report = json.loads((profile / 'smoke-test.json').read_text(encoding='utf-8'))
    assert report['version'] == VERSION and report['tabs'] == 8
    saved = json.loads((profile / 'settings.json').read_text(encoding='utf-8'))['settings']
    assert saved['freeAudio']['volume'] == 37
    assert saved['desktop']['last_version'] == VERSION and saved['desktop']['language'] == 'en'
    assert json.loads((profile / 'freeAudio_favorites.json').read_text())[0]['stationuuid'] == 'fixture'
    assert json.loads((profile / 'podcast_positions.json').read_text())['episode']['position'] == 42.5
    assert (profile / ('backups/profile-before-' + VERSION + '.zip')).is_file()
    print('Installed 1.1.1 -> ' + VERSION + ': settings, favourites, progress, backup and packaged startup OK')


if __name__ == '__main__':
    main()
