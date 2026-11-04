"""Build both distributions from one source tree on Windows x64."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from prepare import prepare
from desktop.version import VERSION

ROOT = Path(__file__).resolve().parent


def source_files(root, build, output):
    """Exclude build outputs and local profiles even for an in-repository build."""
    root, build, output = Path(root).resolve(), Path(build).resolve(), Path(output).resolve()
    excluded = {'.git', '.venv', 'venv', '.build', 'releases', 'data',
                '__pycache__', '.test-profile', '.smoke-profile'}
    for file in sorted(root.rglob('*')):
        if not file.is_file():
            continue
        relative = file.relative_to(root)
        # FFmpeg is an optional external tool, configured through Settings.
        # Do not redistribute the upstream's unmaintained binary.
        if relative.as_posix() == 'vendor/freeAudio/ffmpeg.exe':
            continue
        if any(part in excluded for part in relative.parts) or file.suffix == '.pyc':
            continue
        if build.is_relative_to(root) and file.resolve().is_relative_to(build):
            continue
        if output != root and output.is_relative_to(root) and file.resolve().is_relative_to(output):
            continue
        if len(relative.parts) == 1 and (file.suffix.lower() in ('.zip', '.exe') or file.name.startswith('SHA256SUMS')):
            continue
        yield file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--iscc', type=Path, required=True)
    args = parser.parse_args()
    build = args.build_dir.resolve()
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)
    prepare()
    command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
               '--distpath', str(build / 'dist'), '--workpath', str(build / 'pyinstaller'),
               str(ROOT / 'freeAudioDesktop.spec')]
    subprocess.run(command, check=True, cwd=ROOT)
    stage = build / 'dist/freeAudioDesktop'
    (stage / 'portable.flag').write_text('Portable data directory: ./data\n', encoding='utf-8')
    shutil.copyfile(ROOT / 'README.md', stage / 'README.md')
    portable = output / f'freeAudio-Desktop-{VERSION}-win64-portable.zip'
    with zipfile.ZipFile(portable, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for file in sorted(stage.rglob('*')):
            if file.is_file() and 'data' not in file.relative_to(stage).parts and '__pycache__' not in file.parts:
                archive.write(file, Path('freeAudioDesktop') / file.relative_to(stage))
    subprocess.run([str(args.iscc.resolve()), '/Qp', '/DStageDir=' + str(stage),
                    '/DReleaseDir=' + str(output), '/DAppVersion=' + VERSION,
                    str(ROOT / 'installer.iss')], check=True)
    source_zip = output / f'freeAudio-Desktop-{VERSION}-source.zip'
    with zipfile.ZipFile(source_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for file in source_files(ROOT, build, output):
            archive.write(file, Path('freeAudio-desktop') / file.relative_to(ROOT))
    deliverables = [portable, source_zip, output / f'freeAudio-Desktop-{VERSION}-win64-setup.exe']
    (output / 'SHA256SUMS.txt').write_text(''.join(
        hashlib.file_digest(file.open('rb'), 'sha256').hexdigest() + '  ' + file.name + '\n'
        for file in deliverables), encoding='ascii')
    print('\n'.join(str(file) for file in deliverables))


if __name__ == '__main__':
    main()
