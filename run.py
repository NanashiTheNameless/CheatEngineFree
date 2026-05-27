#!/usr/bin/env python3
import os
import sys
import platform
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from datetime import datetime, timezone, timedelta
import subprocess
import shlex
import shutil


def create_desktop_entry(ce_path: str, name: str = None, icon: str = None):
    """Create a .desktop file in the current user's applications folder that launches Cheat Engine
    via our launcher (so network will be blocked when launched).
    """
    home = Path.home()
    applications_dir = home / '.local' / 'share' / 'applications'
    applications_dir.mkdir(parents=True, exist_ok=True)

    if name is None:
        name = 'Cheat Engine Offline'

    launcher = Path(__file__).parent / 'tools' / 'linux' / 'ce_launcher.sh'
    exec_cmd = f'{launcher} "{ce_path}" %U'

    if icon is None:
        try:
            import urllib.request

            icons_dir = home / '.local' / 'share' / 'icons' / 'cheat-engine'
            icons_dir.mkdir(parents=True, exist_ok=True)
            default_url = 'https://raw.githubusercontent.com/cheat-engine/cheat-engine/master/Cheat%20Engine/images/celogo.png'
            icon_path = icons_dir / 'celogo.png'
            if not icon_path.exists():
                urllib.request.urlretrieve(default_url, str(icon_path))
            icon = str(icon_path)
        except Exception:
            icon = None

    slug = name.lower().replace(' ', '-').replace('/', '-')
    desktop_path = applications_dir / f"{slug}.desktop"

    lines = [
        '[Desktop Entry]',
        f'Name={name}',
        'Type=Application',
        f'Exec={exec_cmd}',
        'Terminal=false',
        'StartupNotify=false',
        'Categories=Utility;Game;'
    ]

    if icon:
        lines.insert(3, f'Icon={icon}')

    desktop_text = '\n'.join(lines) + '\n'
    desktop_path.write_text(desktop_text, encoding='utf-8')
    desktop_path.chmod(0o644)
    print(f"Created desktop entry: {desktop_path}")


def compute_lastcheck_hours_offset(hours=-26):
    now = datetime.now(timezone.utc)
    target = now + timedelta(hours=hours)
    return int(target.timestamp())


def compute_lastcheck_days_offset(days=-3):
    now = datetime.now(timezone.utc)
    target = now + timedelta(days=days)
    return int(target.timestamp())


def build_settings():
    return [
        {"name": "cesession", "value": "0", "type": "REG_SZ"},
        {"name": "lastcheck", "value": compute_lastcheck_days_offset(-3), "type": "REG_DWORD"},
    ]


WINDOWS_REG_ROOT = r"Software\\CEPatreon"
WINDOWS_REG_HIVE = "HKCU"


XML_PATH = Path.home() / ".config" / "Cheat Engine" / "Cheat Engine" / "reg.xml"
XML_ROOT_NAME = "settings"


def write_windows_registry(settings):
    import winreg

    hive_map = {
        "HKCU": winreg.HKEY_CURRENT_USER,
        "HKLM": winreg.HKEY_LOCAL_MACHINE,
    }

    if WINDOWS_REG_HIVE not in hive_map:
        raise ValueError(f"Unsupported registry hive: {WINDOWS_REG_HIVE}")

    hive = hive_map[WINDOWS_REG_HIVE]

    with winreg.CreateKeyEx(hive, WINDOWS_REG_ROOT, 0, winreg.KEY_SET_VALUE) as key:
        for item in settings:
            name = item["name"]
            value = item["value"]
            value_type = item.get("type", "string").lower()
            if value_type.startswith("reg_"):
                value_type = value_type[4:]

            if value_type == "string":
                reg_type = winreg.REG_SZ
                reg_value = str(value)

            elif value_type == "dword":
                reg_type = winreg.REG_DWORD
                reg_value = int(value)

            elif value_type == "qword":
                reg_type = winreg.REG_QWORD
                reg_value = int(value)

            elif value_type == "binary":
                reg_type = winreg.REG_BINARY
                if isinstance(value, bytes):
                    reg_value = value
                else:
                    reg_value = bytes.fromhex(str(value))

            else:
                raise ValueError(f"Unsupported registry value type: {value_type}")

            winreg.SetValueEx(key, name, 0, reg_type, reg_value)
            print(f"Set registry value: {WINDOWS_REG_HIVE}\\{WINDOWS_REG_ROOT}\\{name}")


def indent_xml(elem, level=0):
    indent = "\n" + level * "  "
    child_indent = "\n" + (level + 1) * "  "

    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = child_indent

        for child in elem:
            indent_xml(child, level + 1)

        if not elem.tail or not elem.tail.strip():
            elem.tail = indent
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = indent


def write_xml_settings(settings):
    XML_PATH.parent.mkdir(parents=True, exist_ok=True)

    if XML_PATH.exists():
        from shutil import copyfile

        backup_bak = XML_PATH.with_name("reg.xml.bak")
        copyfile(XML_PATH, backup_bak)
        print(f"Backed up existing reg.xml to: {backup_bak}")

        try:
            tree = ET.parse(XML_PATH)
            root = tree.getroot()
        except ET.ParseError:
            root = ET.Element("XMLReg")
            tree = ET.ElementTree(root)
    else:
        root = ET.Element("XMLReg")
        tree = ET.ElementTree(root)

    hkcu = root.find("./Key[@Name='HKEY_CURRENT_USER']")
    if hkcu is None:
        hkcu = ET.SubElement(root, 'Key')
        hkcu.set('Name', 'HKEY_CURRENT_USER')

    software = hkcu.find("./Key[@Name='Software']")
    if software is None:
        software = ET.SubElement(hkcu, 'Key')
        software.set('Name', 'Software')

    cheat = None
    for child in software.findall('Key'):
        if child.get('Name') == 'Cheat Engine':
            cheat = child
            break
    if cheat is None:
        cheat = ET.SubElement(software, 'Key')
        cheat.set('Name', 'Cheat Engine')

    for parent_candidate in root.findall('.//Key'):
        for child in list(parent_candidate):
            if child.tag == 'Key' and child.get('Name') == 'CEPatreon':
                parent_candidate.remove(child)

    cep_node = ET.SubElement(software, 'Key')
    cep_node.set('Name', 'CEPatreon')

    type_map = {'REG_SZ': '2', 'REG_DWORD': '1'}
    for item in settings:
        val = ET.SubElement(cep_node, 'Value')
        val.set('Name', item['name'])
        val.set('Type', type_map.get(item.get('type', '').upper(), '2'))
        val.text = str(item['value'])
        print(f"Set XML Value: {item['name']} (Type={val.get('Type')})")

    ces_val = next((str(i['value']) for i in settings if i['name'] == 'cesession'), '0')
    last_val = next((str(i['value']) for i in settings if i['name'] == 'lastcheck'), '')

    out = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<XMLReg>\n'
        '  <Key Name="HKEY_CURRENT_USER">\n'
        '    <Key Name="Software">\n'
        '      <Key Name="Cheat Engine">\n'
        '        <Value Name="Init" Type="2">123</Value>\n'
        '        <Key Name="Hexview"/>\n'
        '        <Key Name="dotnetinfo"/>\n'
        '        <Key Name="MonoExtension">\n'
        '          <Value Name="EnableUsesMonoOptionOnAttach" Type="1">1</Value>\n'
        '        </Key>\n'
        '        <Key Name="VersionCheck"/>\n'
        '        <Key Name="Java"/>\n'
        '        <Key Name="AITOOLS"/>\n'
        '        <Key Name="AI Tools">\n'
        '          <Value Name="EnableAITools" Type="1">1</Value>\n'
        '        </Key>\n'
        '        <Key Name="Window Positions 96">\n'
        '          <Value Name="Comments Position" Type="2">9B010000180300004F01000001010000</Value>\n'
        '          <Value Name="AdvancedOptions Position" Type="2">380100001502000056030000C7010000</Value>\n'
        '          <Value Name="MainForm Position" Type="2">F4000000300200001F0300005002000028000000A0000000550000003C00000010270000FE01000036000000</Value>\n'
        '          <Value Name="frmLuaTableScript Position" Type="2">7F010000E8020000AF01000039010000</Value>\n'
        '        </Key>\n'
        '        <Key Name="Ignored Exceptions"/>\n'
        '      </Key>\n'
        '      <Key Name="CEPatreon">\n'
        f'        <Value Name="cesession" Type="2">{ces_val}</Value>\n'
        f'        <Value Name="lastcheck" Type="1">{last_val}</Value>\n'
        '      </Key>\n'
        '    </Key>\n'
        '    <Key Name="Cookies"/>\n'
        '  </Key>\n'
        '</XMLReg>\n'
    )

    XML_PATH.write_text(out, encoding='utf-8')
    print(f"Wrote XML (hard-coded style) to: {XML_PATH}")
    return

    indent_xml(root)
    xml_body = ET.tostring(root, encoding='utf-8').decode('utf-8')
    xml_body = xml_body.replace(' />', '/>')
    decl = '<?xml version="1.0" encoding="utf-8"?>\n'
    text = decl + xml_body
    XML_PATH.write_text(text, encoding='utf-8')
    print(f"Wrote valid XML to: {XML_PATH}")


def main():
    USAGE = '''Usage: run.py [--dry-run] [--launch-ce /path/to/CE [args...]] [--create-desktop /path/to/CE [--name NAME] [--icon ICON]]

Options:
  --dry-run             Show computed settings without writing changes
  --launch-ce <path>    Launch Cheat Engine via launcher and update settings after run
  --create-desktop <p>  Create a .desktop entry (Linux only). Use --name and --icon to customize
  -h, --help            Show this help message
'''
    if '-h' in sys.argv or '--help' in sys.argv:
        print(USAGE)
        return

    if "--dry-run" in sys.argv:
        settings = build_settings()
        system = platform.system()
        print("Dry run summary:")
        print(f"- Detected platform: {system}")
        print(f"- Computed settings:")
        for s in settings:
            print(f"  - {s['name']}: {s['value']} (type={s['type']})")

        if system.lower() == "windows":
            print(f"- Action: Will write these values to the Windows registry under {WINDOWS_REG_HIVE}\\{WINDOWS_REG_ROOT} using the types shown.")
            print("  (Requires access to the specified hive; HKLM needs admin rights.)")
        elif system.lower() in {"linux", "darwin"}:
            print(f"- Action: Will write these values into the XML file at: {XML_PATH}")
            if XML_PATH.exists():
                backup_bak = XML_PATH.with_name("reg.xml.bak")
                print(f"  - Existing file detected: {XML_PATH}")
                print(f"  - Will back it up in-place to: {backup_bak}")
            else:
                print(f"  - No existing file at {XML_PATH}; will create a new one with the expected structure.")
            print("  - The script will add a `CEPatreon` key under Software/Cheat Engine and set the values shown.")
        else:
            print("- Action: Unsupported platform for automatic changes.")

        print("Dry run complete. No changes were made.")
        return

    system = platform.system().lower()

    if system == 'linux':
        pass
    elif system == 'darwin':
        if not shutil.which('luluctl'):
            print('Note: macOS network blocking requires LuLu or Little Snitch. Install LuLu (luluctl) or configure Little Snitch to block Cheat Engine.', file=sys.stderr)

    if "--launch-ce" in sys.argv:
        try:
            idx = sys.argv.index("--launch-ce")
            ce_path = sys.argv[idx + 1]
        except Exception:
            print("Usage: --launch-ce /path/to/CheatEngine [args...]", file=sys.stderr)
            sys.exit(2)

        extra_args = []
        try:
            pos = sys.argv.index(ce_path)
            extra_args = sys.argv[pos+1:]
        except Exception:
            extra_args = []

        if system == 'linux':
            launcher = Path(__file__).parent / 'tools' / 'linux' / 'ce_launcher.sh'
            cmd = [str(launcher), ce_path] + extra_args
            print(f"Launching Cheat Engine with blocker: {' '.join(cmd)}")
            os.execv(str(launcher), cmd)

        elif system == 'darwin':
            if shutil.which('luluctl'):
                rule_add = ['sudo', 'luluctl', 'rule', 'add', '--process', ce_path, '--outgoing', 'deny']
                print('Adding LuLu rule to block outgoing for process')
                subprocess.run(rule_add)
                p = subprocess.Popen([ce_path] + extra_args)
                p.wait()
                subprocess.run(['sudo', 'luluctl', 'rule', 'remove', '--process', ce_path])
            else:
                print('No luluctl found; please use Little Snitch or LuLu GUI to block Cheat Engine')
                subprocess.run([ce_path] + extra_args)

        elif system == 'windows':
            ps1 = Path(__file__).parent / 'tools' / 'windows' / 'block_cheatengine.ps1'
            if not ps1.exists():
                print(f"Firewall helper not found: {ps1}", file=sys.stderr)
                sys.exit(1)

            add_cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(ps1), '-Action', 'add', '-ExePath', ce_path]
            rem_cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(ps1), '-Action', 'remove', '-ExePath', ce_path]

            try:
                subprocess.run(add_cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Failed to add firewall rule: {e}", file=sys.stderr)

            try:
                p = subprocess.Popen([ce_path] + extra_args)
                p.wait()
            finally:
                try:
                    subprocess.run(rem_cmd, check=False)
                except Exception:
                    pass

        else:
            subprocess.run([ce_path] + extra_args)

        if system in {'linux', 'darwin'}:
            write_xml_settings(build_settings())
        else:
            write_windows_registry(build_settings())

        return

    if "--create-desktop" in sys.argv:
        try:
            idx = sys.argv.index("--create-desktop")
            ce_path = sys.argv[idx + 1]
        except Exception:
            print("Usage: --create-desktop /path/to/CheatEngine [--name 'Name'] [--icon /path/to/icon.png]", file=sys.stderr)
            sys.exit(2)

        name = None
        icon = None
        if '--name' in sys.argv:
            try:
                name = sys.argv[sys.argv.index('--name') + 1]
            except Exception:
                name = None
        if '--icon' in sys.argv:
            try:
                icon = sys.argv[sys.argv.index('--icon') + 1]
            except Exception:
                icon = None

        if system != 'linux':
            print('Desktop entry creation currently supported on Linux only.', file=sys.stderr)
            sys.exit(1)

        create_desktop_entry(ce_path, name=name, icon=icon)
        sys.exit(0)

    if system == "windows":
        write_windows_registry(build_settings())

    elif system in {"linux", "darwin"}:
        write_xml_settings(build_settings())

    else:
        raise RuntimeError(f"Unsupported platform: {platform.system()}")


if __name__ == "__main__":
    try:
        main()
    except PermissionError:
        print("Permission denied. On Windows, HKLM requires Administrator rights.", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)