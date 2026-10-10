#!/usr/bin/env python3
"""dotskills installer.

Symlinks (default) or copies every skill under skills/<name>/SKILL.md into
the Claude Code skills directory so the harness discovers them on the next
launch. Cross-platform: handles Windows symlink quirks via `mklink /D`.

Usage:
    python install.py                       # link all skills to ~/.claude/skills
    python install.py my-skill another      # link only the named skills
    python install.py --copy                # copy instead of symlink
    python install.py --path <dir>          # install into <dir> instead of ~/.claude/skills
    python install.py --uninstall [names]   # remove installed skills
    python install.py --list                # print discovered skills and exit
    python install.py --help
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
SKILLS_DIR = REPO_ROOT / "skills"
DEFAULT_TARGET = Path.home() / ".claude" / "skills"

IS_WINDOWS = os.name == "nt"

# Force UTF-8 I/O so error messages from Windows system calls (which arrive
# in the system codepage) render correctly regardless of the terminal.
if IS_WINDOWS:
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
        sys.stderr.reconfigure(encoding="utf-8", errors="backslashreplace")
    except (AttributeError, OSError):
        pass

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RESET = "\033[0m"


def colorize(text: str, color: str) -> str:
    if sys.stdout.isatty():
        return f"{color}{text}{RESET}"
    return text


def info(msg: str) -> None:
    print(f"{colorize('->', GREEN)} {msg}")


def skip(msg: str) -> None:
    print(f"{colorize('==', YELLOW)} {msg}")


def warn(msg: str) -> None:
    print(f"{colorize('!!', YELLOW)} {msg}")


def error(msg: str) -> None:
    print(f"{colorize('xx', RED)} {msg}", file=sys.stderr)


def discover_skills() -> list[Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(p for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file())


def read_skill_name(skill_dir: Path) -> str | None:
    skill_md = skill_dir / "SKILL.md"
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    return None


def validate_skill(skill_dir: Path) -> tuple[bool, str]:
    """Returns (is_valid, message). Message is the declared name when valid."""
    declared = read_skill_name(skill_dir)
    if declared is None:
        return False, "no `name:` in SKILL.md frontmatter"
    if declared != skill_dir.name:
        return False, f"`name:` is `{declared}` but directory is `{skill_dir.name}`"
    return True, declared


def remove_existing(path: Path) -> None:
    """Best-effort removal of an existing file, symlink, or empty/non-empty dir."""
    if not path.exists() and not path.is_symlink():
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    if path.is_dir():
        if IS_WINDOWS:
            subprocess.run(["cmd", "/c", "rmdir", str(path)],
                           check=False, capture_output=True)
            if path.exists():
                shutil.rmtree(path, ignore_errors=True)
        else:
            shutil.rmtree(path)


def _decode(data: bytes) -> str:
    if not data:
        return ""
    for enc in ("utf-8", "gbk", "mbcs"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def symlink_windows(source: Path, target: Path) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/D", str(target), str(source)],
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"mklink failed: {e}"
    if result.returncode != 0:
        stderr = _decode(result.stderr).strip()
        stdout = _decode(result.stdout).strip()
        return False, stderr or stdout or "mklink exit nonzero"
    return True, ""


def symlink(source: Path, target: Path) -> tuple[bool, str]:
    if not IS_WINDOWS:
        try:
            os.symlink(source, target)
            return True, ""
        except OSError as e:
            return False, str(e)

    remove_existing(target)
    ok, msg = symlink_windows(source, target)
    if ok:
        return True, ""

    try:
        os.symlink(source, target)
        return True, ""
    except OSError as e:
        return False, f"{msg}; os.symlink also failed: {e}"


def copy_tree(source: Path, target: Path) -> tuple[bool, str]:
    try:
        remove_existing(target)
        shutil.copytree(source, target)
        return True, ""
    except OSError as e:
        return False, str(e)


def install_one(source: Path, target_dir: Path, use_copy: bool) -> tuple[bool, str]:
    target = target_dir / source.name
    target_dir.mkdir(parents=True, exist_ok=True)

    if use_copy:
        ok, msg = copy_tree(source, target)
        return (True, f"copied to {target}") if ok else (False, f"copy failed: {msg}")

    if target.is_symlink():
        try:
            existing = os.readlink(target)
        except OSError:
            existing = None
        if existing and Path(existing).resolve() == source.resolve():
            return True, "already linked"
        remove_existing(target)

    ok, msg = symlink(source, target)
    if not ok:
        return False, f"symlink failed: {msg}; re-run with --copy if this persists"
    return True, "linked"


def uninstall_one(target_dir: Path, name: str) -> tuple[bool, str]:
    target = target_dir / name
    if not target.exists() and not target.is_symlink():
        return False, "not installed"
    try:
        if target.is_symlink():
            target.unlink()
        elif target.is_dir():
            if IS_WINDOWS:
                subprocess.run(["cmd", "/c", "rmdir", str(target)],
                               check=False, capture_output=True)
            shutil.rmtree(target, ignore_errors=True)
        else:
            target.unlink()
    except OSError as e:
        return False, str(e)
    if target.exists():
        return False, f"still present after removal: {target}"
    return True, "removed"


def run(args: argparse.Namespace) -> int:
    target = Path(args.path).expanduser().resolve() if args.path else DEFAULT_TARGET

    skills = discover_skills()
    if args.list:
        if not skills:
            skip(f"no skills found under {SKILLS_DIR}")
            return 0
        info(f"found {len(skills)} skill(s) under {SKILLS_DIR}:")
        for s in skills:
            ok, msg = validate_skill(s)
            tag = colorize(s.name, GREEN) if ok else colorize(s.name, YELLOW)
            note = "" if ok else f"  {colorize('(warning: ' + msg + ')', YELLOW)}"
            print(f"  - {tag}{note}")
        return 0

    if args.uninstall:
        names = list(args.skills) if args.skills else [s.name for s in skills]
        failures = 0
        for name in names:
            ok, msg = uninstall_one(target, name)
            if ok:
                info(f"uninstalled {name} from {target} ({msg})")
            elif msg == "not installed":
                skip(f"{name}: {msg}")
            else:
                error(f"{name}: {msg}")
                failures += 1
        return 0 if failures == 0 else 1

    if not skills:
        error(f"no skills found under {SKILLS_DIR}")
        return 1

    selected = skills
    if args.skills:
        wanted = set(args.skills)
        selected = [s for s in skills if s.name in wanted]
        for m in sorted(wanted - {s.name for s in selected}):
            warn(f"requested skill not found: {m}")

    if not selected:
        error("nothing to install")
        return 1

    mode = "copy" if args.copy else "link"
    info(f"installing {len(selected)} skill(s) into {target} (mode: {mode})")

    failures = 0
    warnings = 0
    for s in selected:
        ok, msg = validate_skill(s)
        if not ok:
            warn(f"{s.name}: {msg} (installing anyway)")
            warnings += 1
        ok, msg = install_one(s, target, args.copy)
        if ok:
            info(f"{s.name}: {msg}")
        else:
            error(f"{s.name}: {msg}")
            failures += 1

    if failures:
        return 1
    if warnings:
        return 2
    print()
    print(colorize("done.", GREEN),
          f"restart Claude Code (or run it from {target.parent}) to pick up changes.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="install.py",
        description="Install dotskills into Claude Code's skills directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="examples:\n"
               "  python install.py\n"
               "  python install.py i-have-adhd\n"
               "  python install.py --copy --path ./test-skills\n"
               "  python install.py --uninstall i-have-adhd\n",
    )
    p.add_argument("skills", nargs="*",
                   help="specific skill names to install (default: all)")
    p.add_argument("--copy", action="store_true",
                   help="copy skill directories instead of symlinking")
    p.add_argument("--path", metavar="DIR",
                   help=f"install into DIR (default: {DEFAULT_TARGET})")
    p.add_argument("--uninstall", action="store_true",
                   help="remove installed skills; with names, only those")
    p.add_argument("--list", action="store_true",
                   help="list discovered skills and exit")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.uninstall and args.copy:
        error("--uninstall and --copy are mutually exclusive")
        return 1
    try:
        return run(args)
    except KeyboardInterrupt:
        error("interrupted")
        return 130


if __name__ == "__main__":
    sys.exit(main())
