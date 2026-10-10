# dotskills

Personal collection of Claude Code skills, with a one-shot installer.

## Quick start

```bash
git clone https://github.com/zjbfx/dotskills.git
cd dotskills
python install.py
```

That picks the skill set that matches your OS and symlinks every skill
under `skills/<platform>/` into `~/.claude/skills/`, where Claude Code
discovers them. Editing a `SKILL.md` here takes effect on the next Claude
Code launch — no reinstall.

## Layout

Skills are split by platform so a single repo can carry Windows and Linux
variants side by side. `install.py` auto-detects your OS and only touches
the matching subdir.

```
.
├── README.md
├── install.py
└── skills/
    ├── win/
    │   └── <skill-name>/SKILL.md
    └── linux/
        └── <skill-name>/SKILL.md
```

To add a skill for both platforms, create it under both `skills/win/` and
`skills/linux/`. To add a platform-specific one, only the relevant subdir
needs the entry.

## Skills (currently shipping)

| Name | Platforms | Source |
| --- | --- | --- |
| `i-have-adhd` | win, linux | https://github.com/ayghri/i-have-adhd |
| `powershell-expert` | win | https://github.com/hmohamed01/powershell-expert |

## Usage

```text
python install.py                       install all current-platform skills
python install.py my-skill another      install only the named skills
python install.py --copy                copy instead of symlink
python install.py --path <dir>          install into <dir> instead of ~/.claude/skills
python install.py --platform <p>        act as if running on platform p (win|linux)
python install.py --uninstall [names]   remove installed skills
python install.py --list                list current-platform skills
python install.py --help                full help
```

- Cross-platform: works the same on Windows, macOS, and Linux.
- On Windows, the script uses `mklink /D` so you do not need Developer
  Mode or admin rights. If symlinking still fails (corporate policy, etc.),
  re-run with `--copy`.
- `--platform` is for inspection/cross-platform workflows (e.g. listing
  the Linux set from WSL). By default install and uninstall still target
  the OS you are actually on.

## Exit codes

`0` success &middot; `1` error &middot; `2` warnings (skill name and
directory mismatch, etc.)
