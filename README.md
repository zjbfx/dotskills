# dotskills

Personal collection of Claude Code skills, with a one-shot installer.

## Quick start

```bash
git clone https://github.com/zjbfx/dotskills.git
cd dotskills
python install.py
```

That symlinks every skill under `skills/` into `~/.claude/skills/`, where
Claude Code discovers them. Editing a `SKILL.md` here takes effect on the
next Claude Code launch — no reinstall.

## Skills

| Name | Source |
| --- | --- |
| `i-have-adhd` | https://github.com/ayghri/i-have-adhd |

Drop new skills into `skills/<name>/SKILL.md`; the installer picks them up
automatically.

## Usage

```text
python install.py                       install all skills
python install.py my-skill another      install only the named skills
python install.py --copy                copy instead of symlink
python install.py --path <dir>          install into <dir> instead of ~/.claude/skills
python install.py --uninstall [names]   remove installed skills
python install.py --list                list discovered skills
python install.py --help                full help
```

`-` cross-platform: works the same on Windows, macOS, and Linux.
`-` on Windows, the script uses `mklink /D` so you do not need Developer
  Mode or admin rights. If symlinking still fails (corporate policy, etc.),
  re-run with `--copy`.

## Exit codes

`0` success &middot; `1` error &middot; `2` warnings (skill name and
directory mismatch, etc.)

## Repository layout

```
.
├── README.md
├── install.py
└── skills/
    └── i-have-adhd/
        └── SKILL.md
```
