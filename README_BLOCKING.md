Per-process network blocking helpers for Cheat Engine

Linux
- Preferred: per-UID kernel filtering via `nft` (nftables) or `iptables`.

Scripts
- `tools/linux/ce_launcher.sh /path/to/cheatengine [args...]` -- launches Cheat Engine and temporarily installs a per-UID `nft`/`iptables` rule to drop outbound traffic for the process's UID. The launcher will prompt for elevation via `pkexec` or `sudo` when required.

Windows
- `tools/windows/block_cheatengine.ps1 -Action add -ExePath 'C:\Path\cheatengine.exe'` adds a firewall rule to block outbound traffic for the executable (requires admin).
- `tools/windows/block_cheatengine.ps1 -Action remove -ExePath 'C:\Path\cheatengine.exe'` removes the rule.

macOS
- See `tools/macos/README_BLOCKING.md` for instructions for Little Snitch and LuLu. CLI automation is possible if `luluctl` or Little Snitch CLIs are present.

Possible next steps:
- Integrate these launchers into `run.py` so it can spawn Cheat Engine with blocking automatically.
- Add unit tests or a small demo launcher.