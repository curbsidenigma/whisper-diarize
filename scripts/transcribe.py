#!/usr/bin/env python3
"""
Transcribe all audio files in a folder using faster-whisper on GPU.
Usage:
    python transcribe.py ./input ./output
    python transcribe.py ./input ./output --prompt "Context about the audio"
"""
import argparse
import shutil
import sys
from pathlib import Path
from faster_whisper import WhisperModel

AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".flac", ".ogg", ".opus", ".aac", ".mp4"}


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS for progress output."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def move_to_done(audio: Path, input_dir: Path) -> None:
    """Move a processed recording into <input_dir>/done/, keeping its name."""
    done_dir = input_dir / "done"
    done_dir.mkdir(exist_ok=True)
    # shutil.move, not Path.rename: input/ and done/ may be on different mounts.
    shutil.move(str(audio), str(done_dir / audio.name))
    print(f"  moved to {done_dir}/")


def main():
    parser = argparse.ArgumentParser(description="Transcribe audio files with faster-whisper")
    parser.add_argument("input_dir", help="Folder containing audio files")
    parser.add_argument("output_dir", help="Output folder for transcripts")
    parser.add_argument("--model", default="large-v3", help="Model size (default: large-v3)")
    parser.add_argument("--language", default="es", help="Audio language code (default: es)")
    parser.add_argument("--prompt", default="", help="Optional initial prompt for context")
    parser.add_argument("--compute-type", default="float16",
                        choices=["float16", "int8_float16", "int8"],
                        help="Compute precision (default: float16)")
    parser.add_argument("--keep-audio", action="store_true",
                        help="Leave the audio in place instead of moving it "
                             "to <input_dir>/done/ after a successful run")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_files = sorted(
        [f for f in input_dir.iterdir() if f.suffix.lower() in AUDIO_EXTS]
    )
    if not audio_files:
        print(f"No audio files found in {input_dir}")
        sys.exit(1)

    print(f"Loading model {args.model} on GPU ({args.compute_type})...")
    model = WhisperModel(args.model, device="cuda", compute_type=args.compute_type)
    print(f"Processing {len(audio_files)} file(s)\n")

    for i, audio in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] {audio.name}")
        segments, info = model.transcribe(
            str(audio),
            language=args.language,
            initial_prompt=args.prompt or None,
            beam_size=5,
            vad_filter=True,  # filters silences, prevents hallucinations
        )
        print(f"  Duration: {info.duration:.1f}s | Language confidence: {info.language_probability:.2f}")

        txt_path = output_dir / f"{audio.stem}.txt"

        with open(txt_path, "w", encoding="utf-8") as f_txt:
            for seg in segments:
                f_txt.write(seg.text.strip() + "\n")
                print(f"  [{format_timestamp(seg.start)}] {seg.text.strip()[:80]}")

        print(f"  -> {txt_path.name}")
        if not args.keep_audio:
            move_to_done(audio, input_dir)
        print()

    print("Done.")


if __name__ == "__main__":
    main()
