#!/usr/bin/env python3
"""
Screenshot Deletion Bot
Manually run this script to find and delete screenshots from your macOS Desktop.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path


DESKTOP = Path.home() / "Desktop"

# macOS default screenshot filename patterns and extensions
SCREENSHOT_PATTERNS = ("Screenshot", "Screen Shot", "screen-", "screenshot")
SCREENSHOT_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def find_screenshots(older_than_days: int | None = None) -> list[Path]:
    """Find screenshot files on the Desktop matching patterns and extensions."""
    matches = []
    cutoff = datetime.now() - timedelta(days=older_than_days) if older_than_days is not None else None

    for file in DESKTOP.iterdir():
        if not file.is_file():
            continue
        if file.suffix.lower() not in SCREENSHOT_EXTENSIONS:
            continue
        if not any(file.name.startswith(p) for p in SCREENSHOT_PATTERNS):
            continue
        if cutoff is not None:
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            if mtime >= cutoff:
                continue
        matches.append(file)

    return sorted(matches, key=lambda f: f.stat().st_mtime, reverse=True)


def format_size(bytes_: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


def format_mtime(path: Path) -> str:
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return mtime.strftime("%Y-%m-%d %H:%M")


def preview_files(files: list[Path]) -> None:
    if not files:
        print("\n  No screenshots found matching the current filter.\n")
        return

    total_size = sum(f.stat().st_size for f in files)
    print(f"\n  Found {len(files)} screenshot(s)  |  Total size: {format_size(total_size)}\n")
    print(f"  {'#':<4}  {'Date Modified':<17}  {'Size':>8}  Name")
    print(f"  {'-'*4}  {'-'*17}  {'-'*8}  {'-'*40}")
    for i, f in enumerate(files, 1):
        size = format_size(f.stat().st_size)
        print(f"  {i:<4}  {format_mtime(f):<17}  {size:>8}  {f.name}")
    print()


def confirm_delete(files: list[Path]) -> bool:
    total_size = sum(f.stat().st_size for f in files)
    print(f"\n  You are about to permanently delete {len(files)} file(s) ({format_size(total_size)}).")
    answer = input("  Are you sure? Type 'yes' to confirm: ").strip().lower()
    return answer == "yes"


def delete_files(files: list[Path]) -> None:
    deleted, failed = 0, 0
    for f in files:
        try:
            f.unlink()
            deleted += 1
        except OSError as e:
            print(f"  [ERROR] Could not delete {f.name}: {e}")
            failed += 1
    print(f"\n  Done. {deleted} file(s) deleted.", end="")
    if failed:
        print(f" {failed} file(s) failed.", end="")
    print("\n")


def get_day_filter() -> int | None:
    print("\n  Filter by age — delete screenshots older than how many days?")
    print("  (Press Enter to skip this filter and show all screenshots)")
    raw = input("  Days: ").strip()
    if not raw:
        return None
    try:
        days = int(raw)
        if days <= 0:
            raise ValueError
        return days
    except ValueError:
        print("  Invalid input. Showing all screenshots.")
        return None


def print_header() -> None:
    print("\n" + "=" * 60)
    print("          Screenshot Deletion Bot — macOS Desktop")
    print("=" * 60)


def main_menu() -> None:
    print_header()
    older_than_days: int | None = None

    while True:
        filter_label = f"older than {older_than_days} day(s)" if older_than_days is not None else "all ages"
        print(f"\n  Active filter: {filter_label}")
        print("  Desktop path:", DESKTOP)
        print()
        print("  [1] Preview matching screenshots")
        print("  [2] Filter by age (days)")
        print("  [3] Delete matching screenshots")
        print("  [4] Reset filter (show all)")
        print("  [5] Quit")
        print()

        choice = input("  Choose an option [1-5]: ").strip()

        if choice == "1":
            files = find_screenshots(older_than_days)
            preview_files(files)

        elif choice == "2":
            older_than_days = get_day_filter()

        elif choice == "3":
            files = find_screenshots(older_than_days)
            preview_files(files)
            if files and confirm_delete(files):
                delete_files(files)
            elif files:
                print("\n  Deletion cancelled.\n")

        elif choice == "4":
            older_than_days = None
            print("\n  Filter reset. Showing all screenshots.\n")

        elif choice == "5":
            print("\n  Goodbye!\n")
            sys.exit(0)

        else:
            print("\n  Invalid option. Please choose 1–5.\n")


if __name__ == "__main__":
    if not DESKTOP.exists():
        print(f"[ERROR] Desktop folder not found: {DESKTOP}")
        sys.exit(1)
    main_menu()
