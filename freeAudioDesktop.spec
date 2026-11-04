from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH)
ao_data, ao_binary, ao_hidden = collect_all('accessible_output2')
ll_data, ll_binary, ll_hidden = collect_all('libloader')
a = Analysis(
    [str(root / 'main.py')], pathex=[str(root / 'vendor')],
    binaries=ao_binary + ll_binary,
    datas=ao_data + ll_data + [(str(root / 'locale'), 'locale'),
                             (str(root / 'docs'), 'docs'),
                             (str(root / 'LICENSE'), '.'),
                             (str(root / 'release-channel.json'), '.'),
                             (str(root / 'THIRD-PARTY.md'), '.')],
    hiddenimports=ao_hidden + ll_hidden + ['comtypes.client', 'comtypes.stream',
                                         'comtypes.gen.SpeechLib'],
    hookspath=[], runtime_hooks=[], excludes=[], noarchive=False,
)
# Keep the audio worker's embedded Python distribution isolated. Adding it
# after Analysis prevents binary reclassification from mixing its OpenSSL DLLs
# into the GUI interpreter's DLL directory.
a.datas += Tree(str(root / 'vendor'), prefix='vendor',
                excludes=['__pycache__', '*.pyc', 'ffmpeg.exe'], typecode='DATA')
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='freeAudioDesktop',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False,
          manifest=str(root / 'app.manifest'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='freeAudioDesktop')
