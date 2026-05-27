#!/usr/bin/env python3
import shutil
import subprocess
import sys
from pathlib import Path


REPO = 'https://github.com/NanashiTheNameless/CheatEngineFree.git'
DEST = Path.home() / 'CheatEngineFree'


def main():
    if DEST.exists():
        git_dir = DEST / '.git'
        if git_dir.exists():
            print(f'Destination {DEST} exists - updating via git pull')
            try:
                subprocess.run(['git', '-C', str(DEST), 'pull', '--ff-only'], check=True)
            except subprocess.CalledProcessError as e:
                print('git pull failed:', e)
                sys.exit(e.returncode)
            print('Update complete.')
            print('\nNext steps:')
            print(f'  cd {DEST}')
            print('  python3 run.py --help')
            print('  python3 run.py --dry-run')
            return
        else:
            print(f'Destination exists and is not a git repo: {DEST} - aborting')
            sys.exit(1)

    if shutil.which('git') is None:
        print('git required but not found in PATH')
        sys.exit(1)

    print(f'Cloning {REPO} -> {DEST}')
    try:
        subprocess.run(['git', 'clone', REPO, str(DEST)], check=True)
    except subprocess.CalledProcessError as e:
        print('git clone failed:', e)
        sys.exit(e.returncode)

    print('\nClone complete.')

    import platform

    system = platform.system().lower()
    print('\nNext steps:')
    print(f'  cd {DEST}')

    if system == 'windows':
        print('  py run.py --help')
        print('  py run.py --dry-run')
        print("  # To modify the Windows registry or add firewall rules, run PowerShell as Administrator when required.")
        print("  # Example: py run.py --launch-ce 'C:\\Path\\to\\cheatengine.exe'")

    elif system == 'darwin':
        print('  python3 run.py --help')
        print('  python3 run.py --dry-run')
        print("  python3 run.py --launch-ce /Applications/CheatEngine.app/Contents/MacOS/CheatEngine")

    else:
        print('  python3 run.py --help')
        print('  python3 run.py --dry-run')
        print("  python3 run.py --launch-ce /path/to/CheatEngine")
        print('  python3 run.py --create-desktop /path/to/CheatEngine --name "Cheat Engine Offline"')


if __name__ == '__main__':
    main()
