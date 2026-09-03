#!/usr/bin/env python3
"""
Interactively rename SPEAKER_XX labels in _speakers.txt files to real names.

For each file, shows sample lines per speaker so you can identify who is who,
then prompts you to assign a name to each speaker label.

Usage:
    python rename_speakers.py output/
    python rename_speakers.py output/ --samples 3
"""
import argparse
import re
import sys
from pathlib import Path
from collections import defaultdict


SPEAKER_PATTERN = re.compile(r"\[(\d{2}:\d{2}:\d{2})\] (SPEAKER_\d+|UNKNOWN): (.+)")


def parse_speakers_file(path: Path):
    """Extract speaker turns from a _speakers.txt file."""
    turns = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = SPEAKER_PATTERN.match(line)
            if m:
                timestamp, speaker, text = m.groups()
                turns.append((timestamp, speaker, text))
    return turns


def show_speaker_samples(turns, samples_per_speaker=3):
    """Print sample lines for each speaker to help identify them."""
    speaker_turns = defaultdict(list)
    for t in turns:
        speaker_turns[t[1]].append(t)

    for speaker in sorted(speaker_turns.keys()):
        all_turns = speaker_turns[speaker]
        # Show first N turns of meaningful length
        meaningful = [t for t in all_turns if len(t[2]) > 20] or all_turns
        samples = meaningful[:samples_per_speaker]

        total_chars = sum(len(t[2]) for t in all_turns)
        print(f"\n  === {speaker} === ({len(all_turns)} turns, ~{total_chars} characters)")
        for ts, _, text in samples:
            preview = text[:200] + ("..." if len(text) > 200 else "")
            print(f"  [{ts}] {preview}")


def rename_in_file(path: Path, mapping: dict, in_place: bool = True):
    """Replace SPEAKER labels in file according to mapping."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    for old, new in mapping.items():
        # Whole-word match so SPEAKER_1 does not match inside SPEAKER_10.
        # The replacement is a function, not a string: as a string it would be
        # read as a template and a name containing a backslash would fail.
        content = re.sub(rf"\b{re.escape(old)}\b", lambda _, n=new: n, content)

    if in_place:
        out_path = path
    else:
        out_path = path.with_name(path.stem + "_renamed.txt")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", help="Folder containing _speakers.txt files")
    parser.add_argument("--samples", type=int, default=3,
                        help="Number of sample turns to show per speaker")
    parser.add_argument("--in-place", action=argparse.BooleanOptionalAction,
                        default=True,
                        help="Overwrite files in place (default). Use --no-in-place "
                             "to write <name>_renamed.txt alongside instead.")
    args = parser.parse_args()

    folder = Path(args.folder)
    files = sorted(folder.glob("*_speakers.txt"))
    if not files:
        print(f"No *_speakers.txt files found in {folder}")
        sys.exit(1)

    print(f"Found {len(files)} file(s) to process\n")

    for i, path in enumerate(files, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(files)}] {path.name}")
        print('='*70)

        turns = parse_speakers_file(path)
        if not turns:
            print("  No speaker turns found, skipping.")
            continue

        show_speaker_samples(turns, args.samples)

        # Get unique speakers
        unique_speakers = sorted({t[1] for t in turns})
        print("\n  Assign a name to each speaker (press Enter to leave one unchanged):")

        mapping = {}
        for sp in unique_speakers:
            name = input(f"    {sp} -> ").strip()
            if name:
                mapping[sp] = name

        if not mapping:
            print("  No changes, skipping.")
            continue

        print("\n  About to apply:")
        for old, new in mapping.items():
            print(f"    {old} -> {new}")
        target = "overwriting the file" if args.in_place else "writing a copy"
        if input(f"  Confirm ({target})? [y/N] ").strip().lower() != "y":
            print("  Skipped.")
            continue

        # Apply to _speakers.txt
        out = rename_in_file(path, mapping, in_place=args.in_place)
        print(f"  ✓ Updated: {out.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()