"""Real scope/upgrade checks, restricted to disposable GitHub Windows runners."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import winreg
import xml.etree.ElementTree as ET
import pefile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desktop.updates import find_asset,download_update
from desktop.installation import installation_scope
from desktop.version import VERSION

KEY=r'Software\Microsoft\Windows\CurrentVersion\Uninstall\{6F4D1BD0-00BE-47F5-9B24-5B9932EC8F20}_is1'


def registered(root):
    try:
        with winreg.OpenKey(root,KEY,0,winreg.KEY_READ|winreg.KEY_WOW64_64KEY) as key:
            return Path(winreg.QueryValueEx(key,'InstallLocation')[0]).resolve()
    except FileNotFoundError:
        return None


def wait_for(predicate):
    end=time.monotonic()+30
    while not predicate():
        if time.monotonic()>end:raise AssertionError('Uninstall did not finish')
        time.sleep(.1)


def log_text(path):
    data=path.read_bytes()
    encoding='utf-16' if data.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
    return data.decode(encoding,errors='replace')


def main():
    if os.environ.get('GITHUB_ACTIONS')!='true' or not os.environ.get('RUNNER_TEMP'):
        raise SystemExit('Installer checks only run on disposable GitHub Actions runners.')
    root=Path(os.environ['RUNNER_TEMP'])/('freeAudio-scopes-'+VERSION)
    root.mkdir(exist_ok=True)
    current=root/'application'
    machine=Path(os.environ.get('ProgramW6432',os.environ['ProgramFiles']))/'freeAudio Desktop'
    if registered(winreg.HKEY_CURRENT_USER) or registered(winreg.HKEY_LOCAL_MACHINE) or machine.exists():
        raise SystemExit('Unexpected existing installation on the disposable runner')
    profile=root/'roaming/freeAudioDesktop';profile.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,APPDATA=str(profile.parent),FREEAUDIO_SKIP_AUDIO_DEVICE_TEST='1')
    old=download_update(find_asset('selcukucar/freeAudio-desktop','1.2.0'),root/'downloads')
    setup=ROOT/('releases/freeAudio-Desktop-'+VERSION+'-win64-setup.exe')
    # Scope selection must happen before elevation, so legacy Popen updaters work.
    with pefile.PE(str(setup)) as pe:
        levels=[]
        for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if entry.id==24:
                for name in entry.directory.entries:
                    for language in name.directory.entries:
                        data=language.data.struct
                        xml=ET.fromstring(pe.get_data(data.OffsetToData,data.Size).rstrip(b'\0'))
                        levels.extend(node.attrib.get('level') for node in xml.iter()
                                      if node.tag.endswith('requestedExecutionLevel'))
        assert levels and set(levels)=={'asInvoker'},levels

    sequence=[0]
    def install(installer,scope=None,directory=None,expect_success=True):
        sequence[0]+=1
        command=[str(installer),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/NOICONS','/LANG=english',
                 '/LOG='+str(root/('setup-'+str(sequence[0])+'.log'))]
        if scope:command.append('/ALLUSERS' if scope=='all' else '/CURRENTUSER')
        if directory:command.append('/DIR='+str(directory))
        result=subprocess.run(command,env=env,timeout=180)
        assert (result.returncode==0)==expect_success,(command,result.returncode)
        return root/('setup-'+str(sequence[0])+'.log')

    def smoke(directory):
        subprocess.run([str(directory/'freeAudioDesktop.exe'),'--smoke-test'],env=env,check=True,timeout=90)
        report=json.loads((profile/'smoke-test.json').read_text(encoding='utf-8'))
        saved=json.loads((profile/'settings.json').read_text(encoding='utf-8'))['settings']
        assert report['version']==VERSION and report['tabs']==8
        assert report['installation_scope']==installation_scope(directory)
        assert saved['desktop']['last_version']==VERSION and saved['desktop']['language']=='en'
        assert saved['freeAudio']['volume']==37
        assert json.loads((profile/'freeAudio_favorites.json').read_text())[0]['stationuuid']=='fixture'
        assert json.loads((profile/'podcast_positions.json').read_text())['episode']['position']==42.5
        assert (profile/('backups/profile-before-'+VERSION+'.zip')).is_file()
        assert not (directory/'settings.json').exists() and not (directory/'data').exists()

    def uninstall(directory,registry_root):
        subprocess.run([str(directory/'unins000.exe'),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'],
                       env=env,check=True,timeout=180)
        wait_for(lambda:not (directory/'freeAudioDesktop.exe').exists() and registered(registry_root) is None)
        assert (profile/'settings.json').is_file() and (profile/'freeAudio_favorites.json').is_file()

    install(old,directory=current)
    (profile/'settings.json').write_text(json.dumps({'schema_version':1,'settings':{
        'desktop':{'language':'en','last_version':'1.2.0'},
        'freeAudio':{'legacy_migrated':True,'volume':37,'resume_on_start':False,'auto_check_updates':False}}}),encoding='utf-8')
    (profile/'freeAudio_favorites.json').write_text('[{"name":"Upgrade fixture","stationuuid":"fixture"}]')
    (profile/'podcast_positions.json').write_text('{"episode":{"position":42.5,"length":120}}')
    # Emulate the previous updater, which supplies no scope parameter.
    install(setup,directory=current)
    assert installation_scope(current)=='current' and registered(winreg.HKEY_CURRENT_USER)==current.resolve()
    smoke(current)
    install(setup,scope='current',directory=current)
    assert installation_scope(current)=='current'
    conflict=root/'must-not-install-all'
    log=install(setup,scope='all',directory=conflict,expect_success=False)
    assert 'SCOPE_CONFLICT:' in log_text(log)
    assert not conflict.exists()
    uninstall(current,winreg.HKEY_CURRENT_USER)
    print('Legacy/current-user upgrade, explicit scope, conflict prevention and retained Roaming profile: OK',flush=True)

    # With no previous install and no scope/DIR overrides, Program Files must win.
    install(setup)
    assert (machine/'freeAudioDesktop.exe').is_file(),machine
    assert installation_scope(machine)=='all' and registered(winreg.HKEY_LOCAL_MACHINE)==machine.resolve()
    smoke(machine)
    install(setup,scope='all')
    assert installation_scope(machine)=='all'
    conflict=root/'must-not-install-current'
    log=install(setup,scope='current',directory=conflict,expect_success=False)
    assert 'SCOPE_CONFLICT:' in log_text(log)
    assert not conflict.exists()
    uninstall(machine,winreg.HKEY_LOCAL_MACHINE)
    print('Default Program Files/all-users install, upgrade, conflict prevention and unchanged Roaming data: OK',flush=True)


if __name__=='__main__':main()
