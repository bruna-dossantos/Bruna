#!/usr/bin/env python3
"""
organize_run.py  —  package one run's flat output into a named run folder.

Turns a flat directory of `<LCD>_*.ext` files into:

    <Theme> - <Payor> (<ID>)/
      README.md, 1 - Policy Source/, 2 - Working Files/, 3 - Checks/,
      4 - Human Outputs/, 5 - Machine Outputs/

Idempotent. Non-destructive: files it doesn't recognize are left where they are
and listed under "Unsorted" in the README (temp/lock files like ~$* are skipped).

Usage:
  # sort a flat dir into a named run folder next to it
  organize_run.py FLAT_DIR --theme "MRI Head & Neck" --payor "Medicare" --policy-id L37373
  # if FLAT_DIR is already the run folder (root files), it sorts in place
  organize_run.py RUN_DIR  --theme ... --payor ... --in-place
  # pull everything back to the root for a clean re-generation
  organize_run.py RUN_DIR  --flatten
"""

import re
import sys
import shutil
import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import run_layout as L  # noqa: E402


def _skip(name):
    return name.startswith("~$") or name.startswith(".") or name == "README.md"


# obvious superseded/duplicate files — leave at the root, don't file as current output
_ARCHIVE = re.compile(r"^(older|old|copy of|draft|backup|prev|v\d)\b", re.I)


def _is_archive(name):
    return bool(_ARCHIVE.match(name))


def flatten(run_dir):
    """Move every file out of the numbered subfolders back to the run root."""
    run_dir = Path(run_dir)
    moved = 0
    for sub in L.SUBFOLDERS:
        d = run_dir / sub
        if not d.is_dir():
            continue
        for f in d.iterdir():
            if f.is_file() and not _skip(f.name):
                dest = run_dir / f.name
                if dest.exists():
                    dest.unlink()
                shutil.move(str(f), str(dest))
                moved += 1
        # drop the now-empty bucket
        if not any(d.iterdir()):
            d.rmdir()
    print(f"flattened {moved} files back to {run_dir.name}/", file=sys.stderr)
    return moved


def _parse_status(run_dir):
    """Pull the convergence line + review/accepted sections out of the close-loop report."""
    rep = next(run_dir.rglob("*_close_loop_report.md"), None)
    if not rep:
        return None, []
    text = rep.read_text()
    conv = None
    m = re.search(r"^- Converged:\s*(.+)$", text, re.M)
    if m:
        conv = m.group(1).strip().strip("*")
    # grab the NEEDS REVIEW + Accepted residual sections verbatim
    blocks = []
    for header in ("## ⚠ NEEDS REVIEW", "## Accepted residual gaps"):
        i = text.find(header)
        if i == -1:
            continue
        j = text.find("\n## ", i + 1)
        blocks.append(text[i: j if j != -1 else len(text)].strip())
    return conv, blocks


def write_readme(run_dir, folder_name):
    run_dir = Path(run_dir)
    conv, blocks = _parse_status(run_dir)
    lines = [f"# {folder_name}", "",
             "_Auto-generated index for this policy run. Start here._", ""]
    lines.append("## Status")
    if conv:
        lines.append(f"- **Converged:** {conv}")
    else:
        lines.append("- Status: close-loop report not found (run `close_loop.py`).")
    lines.append("")
    if blocks:
        lines.append("## What a reviewer must confirm")
        lines.append("_Everything drafted here is `reviewer: PENDING` until a clinician signs off._\n")
        lines.extend(blocks)
        lines.append("")
    lines.append("## What's in each folder")
    guide = {
        L.POLICY: "The source policy PDFs (LCD / NCD / article) this run was built from.",
        L.WORKING: "Intermediate machine files: the interchange criteria, rule inventory, "
                   "rule locations, and traceability data.",
        L.CHECKS: "The self-check trail: close-loop report, resolutions (definitions for "
                  "vague terms), accepted gaps, resolved criteria, coverage.",
        L.HUMAN: "The read-for-people deliverables: criteria document(s), extraction "
                 "field document(s), and the click-through traceability page.",
        L.MACHINE: "The platform-ready files: criteria JSON with all codes inlined, the "
                   "machine copy, the extraction CSV, and the code sets.",
    }
    for sub in L.SUBFOLDERS:
        d = run_dir / sub
        files = sorted(f.name for f in d.iterdir() if f.is_file() and not _skip(f.name)) if d.is_dir() else []
        lines.append(f"\n### {sub}")
        lines.append(guide[sub])
        for f in files:
            lines.append(f"- `{f}`")
        if not files:
            lines.append("- _(empty)_")
    # unsorted files left at the root
    stray = sorted(f.name for f in run_dir.iterdir()
                   if f.is_file() and not _skip(f.name)
                   and (_is_archive(f.name) or L.bucket_for(f.name) is None))
    if stray:
        lines.append("\n### Unsorted (left at the root)")
        lines.append("_Not recognized by the layout — review and file manually._")
        for f in stray:
            lines.append(f"- `{f}`")
    (run_dir / "README.md").write_text("\n".join(lines) + "\n")
    print(f"wrote {folder_name}/README.md", file=sys.stderr)


def organize(flat_dir, theme, payor, policy_id=None, in_place=False, dest=None):
    flat_dir = Path(flat_dir)
    folder_name = L.run_folder_name(theme, payor, policy_id)
    if in_place:
        run_dir = flat_dir
    else:
        parent = Path(dest) if dest else flat_dir.parent
        run_dir = parent / folder_name
        run_dir.mkdir(parents=True, exist_ok=True)
    for sub in L.SUBFOLDERS:
        (run_dir / sub).mkdir(exist_ok=True)

    moved, stray = 0, 0
    for f in list(flat_dir.iterdir()):
        if not f.is_file() or _skip(f.name):
            continue
        bucket = None if _is_archive(f.name) else L.bucket_for(f.name)
        if bucket is None:
            stray += 1
            if not in_place:  # bring strays along so the run folder is self-contained
                shutil.move(str(f), str(run_dir / f.name))
            continue
        dest_path = run_dir / bucket / f.name
        dest_path.parent.mkdir(exist_ok=True)
        if dest_path.exists():
            dest_path.unlink()
        shutil.move(str(f), str(dest_path))
        moved += 1
    write_readme(run_dir, folder_name)
    print(f"organized {moved} files into {run_dir.name}/ ({stray} unsorted)", file=sys.stderr)
    return run_dir


def main(argv=None):
    ap = argparse.ArgumentParser(description="Package a run's flat output into a named run folder")
    ap.add_argument("dir", help="flat output dir (or the run dir with --in-place / --flatten)")
    ap.add_argument("--theme", help='product/service theme, e.g. "MRI Head & Neck"')
    ap.add_argument("--payor", help='payor, e.g. "Medicare" (be specific if there is no policy ID)')
    ap.add_argument("--policy-id", help="policy identifier, e.g. L37373 (appended in parens)")
    ap.add_argument("--in-place", action="store_true", help="sort files inside the given dir")
    ap.add_argument("--dest", help="parent dir to create the run folder in (default: alongside DIR)")
    ap.add_argument("--flatten", action="store_true",
                    help="reverse: move subfolder files back to the root for re-generation")
    args = ap.parse_args(argv)

    if args.flatten:
        flatten(args.dir)
        return
    if not args.theme or not args.payor:
        ap.error("--theme and --payor are required (unless --flatten)")
    organize(args.dir, args.theme, args.payor, args.policy_id, args.in_place, args.dest)


if __name__ == "__main__":
    main()
