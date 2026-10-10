# dotskills

This repo collects, manages, and installs personal Claude Code skills. Skills
live under `skills/<platform>/<name>/SKILL.md` and are exposed to Claude Code
via `~/.claude/skills/`. When the user asks to install or refresh skills in
this repo, do it directly with shell commands — do not delegate to
`install.py`.

## Layout

```
skills/
  win/<skill-name>/SKILL.md     # Windows variants
  linux/<skill-name>/SKILL.md   # Linux / macOS variants
```

`win` and `linux` are the only platform subdirs. Anything else under
`skills/` is a mistake — point it out instead of installing it.

## Install procedure (you do this, not the user)

When asked to install or refresh skills in this repo:

1. **Detect the current platform.**
   - Windows: `[System.Runtime.InteropServices.RuntimeInformation]::IsOSPlatform(Linux)` is `false`, or `uname` is not on PATH. Default to `win`.
   - Otherwise: `uname -s`. `Darwin` and `Linux` both map to `linux`.
2. **Set the source dir** to `skills/<platform>/` (relative to the repo root).
   The repo root is the directory that contains this file; resolve it
   yourself with `git rev-parse --show-toplevel` or `pwd` if you launched
   from inside the repo.
3. **Set the target dir** to `$HOME/.claude/skills` (Windows: `%USERPROFILE%\.claude\skills`).
   `mkdir -p` it (or `New-Item -ItemType Directory -Force` on Windows PowerShell).
4. **For every directory under the source dir that contains `SKILL.md`:**
   - Target = `<target_dir>/<dir_name>`
   - **Try symlink first**:
     - Windows cmd: `cmd /c mklink /D "<target>" "<source>"`
     - POSIX: `ln -s "<source>" "<target>"`
   - **If symlink fails** (Windows error 1314 / "client does not have
     required privilege"; POSIX `EACCES` / `EPERM` / `ENOTSUP`): **fall
     back to copy** so the user still gets a working install.
     - Windows cmd: `xcopy /E /I /Y "<source>" "<target>"` (after `rmdir`
       if it already exists)
     - POSIX: `cp -R "<source>" "<target>"` (after `rm -rf` if it already
       exists)
   - **If the target already exists and is already the right kind**
     (symlink pointing to source, or an up-to-date copy): **skip** — don't
     re-create it. Use `readlink` (POSIX) or `fsutil reparsepoint query`
     (Windows) to inspect existing symlinks.
5. **Tell the user** which mode you used per skill (linked / copied / skipped)
   and remind them to restart Claude Code (or run it from the target parent)
   to pick up changes.

## Detect what's already installed

If asked "what's installed?" or "did anything change?", list the contents of
the target dir and compare each entry against the source dir.

## Refresh vs full install

- "Install all" / "set up this repo" → loop over the source dir.
- "Refresh / sync" → re-run the loop; existing correct installs are no-ops.
- "Uninstall <name>" → `rm` the target entry (symlinks use `rm`; real
  directories need `rmdir` on Windows or `rm -rf` on POSIX). Confirm with
  the user before uninstalling multiple at once.

## Do not

- Do not edit `SKILL.md` files unless the user asks you to. They came from
  somewhere — read the frontmatter, follow links, and ask before changing.
- Do not run `install.py` on the user's behalf. It is for users who want a
  manual one-shot install. Your job is to install directly.
- Do not use `os.symlink` from a Python script. Use the shell commands
  above so the user sees exactly what ran.
- Do not silently `sudo` / request elevation. If a symlink fails because of
  permissions, fall back to copy and mention it.
- If your shell is MSYS / Git Bash, the `cmd /c "..."` snippet above will
  mis-translate backslashes and quotes. Either:
  - set `MSYS_NO_PATHCONV=1` and `MSYS2_ARG_CONV_EXCL='*'`, use forward
    slashes inside the quoted string, and double every backslash you
    pass to `cmd`, or
  - call the underlying Windows API via PowerShell:
    `powershell -NoProfile -Command "New-Item -ItemType SymbolicLink -Path '<target>' -Target '<source>'"`.

## Reference: parallel Python helper

If a one-shot script is genuinely the cleanest path (e.g. user wants to
script it themselves), the `install.py` at the repo root does the same
thing and supports `--copy`, `--path`, `--platform {win,linux}`,
`--uninstall`, and `--list`. But you should not invoke it; do the install
yourself.
