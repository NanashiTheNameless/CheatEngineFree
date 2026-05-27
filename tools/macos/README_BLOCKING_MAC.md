macOS blocking support (Little Snitch & LuLu)

Overview
- Little Snitch and LuLu are user-mode application firewalls for macOS that allow blocking network access per-application.
- Both have GUIs; LuLu offers a command-line helper when installed via Homebrew (`luluctl`) and Little Snitch provides `littlesnitch` CLI in recent versions (may require admin).

Suggested steps (Little Snitch)
1. Install Little Snitch from https://littlesnitch.com and enable it.
2. Use the GUI to create a rule: deny outgoing network connections for the Cheat Engine binary.
3. If you have Little Snitch CLI available, you can import a ruleset; otherwise use the GUI.

Suggested steps (LuLu)
1. Install LuLu (https://objective-see.org/products/lulu.html) or via Homebrew where available.
2. If `luluctl` is available, you can add a block rule. Example (if luluctl present):

   sudo luluctl rule add --process "/Applications/CheatEngine.app/Contents/MacOS/CheatEngine" --outgoing deny

3. Otherwise, open the LuLu GUI and create a rule blocking outbound connections for the Cheat Engine executable.

Notes
 - These methods are per-application and don't require system-wide firewall changes.
 - Automation depends on the presence of CLI helpers; automated scripting can detect and use `luluctl` or other available CLI tools when present.
