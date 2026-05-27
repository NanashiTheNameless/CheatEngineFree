Per-process network blocking helpers for Cheat Engine

Linux
- Preferred: `firejail --net=none /path/to/cheatengine` (no network for the process).

Scripts
- `tools/linux/firejail_launcher.sh /path/to/cheatengine [args...]` -- launches Cheat Engine under `firejail --net=none`. The launcher will exit with an error if `firejail` is not installed.

Windows
- `tools/windows/block_cheatengine.ps1 -Action add -ExePath 'C:\Path\cheatengine.exe'` adds a firewall rule to block outbound traffic for the executable (requires admin).
- `tools/windows/block_cheatengine.ps1 -Action remove -ExePath 'C:\Path\cheatengine.exe'` removes the rule.

macOS
- See `tools/macos/README_BLOCKING.md` for instructions for Little Snitch and LuLu. CLI automation is possible if `luluctl` or Little Snitch CLIs are present.

Possible next steps:
- Integrate these launchers into `run.py` so it can spawn Cheat Engine with blocking automatically.
- Add unit tests or a small demo launcher.