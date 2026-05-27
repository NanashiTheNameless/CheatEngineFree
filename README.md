# CheatEngineFree

**This work is marked CC0 1.0 Universal. To view a copy of this mark, visit <https://creativecommons.org/publicdomain/zero/1.0/>**

---

**Disclaimer**

- Proof of concept (POC) only: this project is provided for experimentation and study ONLY.
- For lawful, ethical use only: do not access, modify, or test systems without explicit permission.
- Provided "as‑is" with no warranty; the author(s) disclaim all liability for damages arising from use.
- Not actively maintained or supported; no guarantees about stability, security, or updates.
- Use may violate third‑party EULAs, ToS, or local laws—confirm compliance before use.
- May modify configuration or write files; back up important data before running.
- May trigger antivirus or security tools; run in isolated/sandboxed environments when possible.
- Licensed under CC0 1.0 Universal; see the `LICENSE` file for details.

Small tooling to manage Cheat Engine settings (`reg.xml` / registry) and to launch Cheat Engine with per-process network blocking.

Conceptually inspired by <https://github.com/happymimimix/CheatEnginePatreonHack>.

## **Quick summary**

- `setup_tool.py` - idempotent bootstrap: clones/pulls https://github.com/NanashiTheNameless/CheatEngineFree into `~/CheatEngineFree` and prints next steps.
- `run.py` - main helper to update Cheat Engine settings and to launch Cheat Engine with network blocked.
- Linux blocking: requires `firejail` (strict requirement). The launcher and `run.py --launch-ce` will refuse to run without `firejail`.
- macOS: the script will warn about LuLu/Little Snitch; manual setup recommended.


## **Prerequisites**

- Python 3 (for `run.py` / `setup_tool.py`)
- Linux: `firejail` (install via your distro package manager)
- Windows: PowerShell (the repo includes a firewall helper under `tools/windows`)
- macOS: LuLu or Little Snitch recommended for per-process blocking

Usage examples

Clone / bootstrap (runs from any machine):

```bash
# remote bootstrap (clone or update to ~/CheatEngineFree)
curl -fsSL https://github.com/NanashiTheNameless/CheatEngineFree/raw/refs/heads/main/setup_tool.py | python3 -
```

After cloning, run the helper to inspect or apply settings:

```bash
# show computed changes (dry-run)
python3 run.py --dry-run

# apply settings (on Linux/macOS this modifies the reg.xml under ~/.config/Cheat Engine/Cheat Engine/reg.xml)
python3 run.py
```

Launch Cheat Engine with network blocked (Linux only):

```bash
python3 run.py --launch-ce /path/to/CheatEngine [args...]
```

Create a desktop entry (Linux):

```bash
python3 run.py --create-desktop /path/to/CheatEngine --name "Cheat Engine Offline" --icon /path/to/icon.png
```

Notes & safety

- `run.py` writes `CEPatreon`/`cesession` and `lastcheck` values into the expected Cheat Engine settings. When `reg.xml` exists it is backed up in-place to `reg.xml.bak`.
- The repo intentionally requires `firejail` on Linux to ensure per-process network blocking; the launcher will not run without it.
