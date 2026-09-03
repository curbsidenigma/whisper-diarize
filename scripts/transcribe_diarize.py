#!/usr/bin/env python3
"""
Transcribe and diarize audio files using WhisperX.
Outputs both plain transcript and speaker-labeled transcript.

Usage:
    export HF_TOKEN=hf_your_token_here
    python transcribe_diarize.py ./input ./output
    python transcribe_diarize.py ./input ./output --speakers 3
    python transcribe_diarize.py ./input ./output --min-speakers 2 --max-speakers 4
"""
import argparse
import os
import shutil
import sys
import gc
from pathlib import Path

import torch
import whisperx

AUDIO_EXTS = {".m4a", ".mp3", ".wav", ".flac", ".ogg", ".opus", ".aac", ".mp4"}


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def move_to_done(audio_path: Path, input_dir: Path) -> None:
    """Move a processed recording into <input_dir>/done/, keeping its name."""
    done_dir = input_dir / "done"
    done_dir.mkdir(exist_ok=True)
    # shutil.move, not Path.rename: input/ and done/ may be on different mounts.
    shutil.move(str(audio_path), str(done_dir / audio_path.name))
    print(f"  moved to {done_dir}/")


def main():
    parser = argparse.ArgumentParser(description="Transcribe and diarize audio files")
    parser.add_argument("input_dir", help="Folder containing audio files")
    parser.add_argument("output_dir", help="Output folder")
    parser.add_argument("--model", default="large-v3", help="Whisper model size")
    parser.add_argument("--language", default="es", help="Audio language code")
    parser.add_argument("--prompt", default="", help="Optional initial prompt")
    parser.add_argument("--speakers", type=int, default=None,
                        help="Exact number of speakers (if known)")
    parser.add_argument("--min-speakers", type=int, default=None,
                        help="Minimum number of speakers")
    parser.add_argument("--max-speakers", type=int, default=None,
                        help="Maximum number of speakers")
    parser.add_argument("--compute-type", default="float16",
                        choices=["float16", "int8_float16", "int8"])
    parser.add_argument("--batch-size", type=int, default=16,
                        help="Batch size for transcription (lower if OOM)")
    parser.add_argument("--keep-audio", action="store_true",
                        help="Leave the audio in place instead of moving it "
                             "to <input_dir>/done/ after a successful run")
    args = parser.parse_args()

    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        print("ERROR: HF_TOKEN environment variable is required for diarization.")
        print("Get a token at https://huggingface.co/settings/tokens")
        print("Then: export HF_TOKEN=hf_xxxxx")
        sys.exit(1)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audio_files = sorted(
        [f for f in input_dir.iterdir() if f.suffix.lower() in AUDIO_EXTS]
    )
    if not audio_files:
        print(f"No audio files found in {input_dir}")
        sys.exit(1)

    device = "cuda"
    print(f"Loading Whisper model {args.model} ({args.compute_type})...")

    asr_options = {}
    if args.prompt:
        asr_options["initial_prompt"] = args.prompt

    model = whisperx.load_model(
        args.model,
        device=device,
        compute_type=args.compute_type,
        language=args.language,
        asr_options=asr_options if asr_options else None,
    )

    print(f"Processing {len(audio_files)} file(s)\n")

    for i, audio_path in enumerate(audio_files, 1):
        print(f"[{i}/{len(audio_files)}] {audio_path.name}")
        print("  Loading audio...")
        audio = whisperx.load_audio(str(audio_path))

        # 1. Transcribe
        print("  Transcribing...")
        result = model.transcribe(audio, batch_size=args.batch_size, language=args.language)

        # 2. Align (word-level timestamps)
        # The align and diarize models are loaded per file and freed right
        # after, on purpose: holding all three at once does not fit in 8 GB.
        print("  Aligning timestamps...")
        align_model, metadata = whisperx.load_align_model(
            language_code=args.language, device=device
        )
        result = whisperx.align(
            result["segments"], align_model, metadata, audio, device,
            return_char_alignments=False,
        )
        # Free alignment model
        del align_model
        gc.collect()
        torch.cuda.empty_cache()

        # 3. Diarize
        print("  Diarizing speakers...")
        diarize_model = whisperx.diarize.DiarizationPipeline(
            token=hf_token, device=device
        )
        diarize_kwargs = {}
        if args.speakers:
            diarize_kwargs["num_speakers"] = args.speakers
        else:
            if args.min_speakers:
                diarize_kwargs["min_speakers"] = args.min_speakers
            if args.max_speakers:
                diarize_kwargs["max_speakers"] = args.max_speakers

        diarize_segments = diarize_model(audio, **diarize_kwargs)
        result = whisperx.assign_word_speakers(diarize_segments, result)

        del diarize_model
        gc.collect()
        torch.cuda.empty_cache()

        # 4. Write diarized output (grouped by consecutive speaker)
        diarized_path = output_dir / f"{audio_path.stem}_speakers.txt"

        with open(diarized_path, "w", encoding="utf-8") as f_dia:
            current_speaker = None
            current_text = []
            current_start = None

            for seg in result["segments"]:
                text = seg["text"].strip()
                speaker = seg.get("speaker", "UNKNOWN")

                if speaker != current_speaker:
                    if current_speaker is not None:
                        f_dia.write(
                            f"[{format_timestamp(current_start)}] {current_speaker}: "
                            f"{' '.join(current_text)}\n\n"
                        )
                    current_speaker = speaker
                    current_text = [text]
                    current_start = seg["start"]
                else:
                    current_text.append(text)

            if current_speaker is not None:
                f_dia.write(
                    f"[{format_timestamp(current_start)}] {current_speaker}: "
                    f"{' '.join(current_text)}\n\n"
                )

        speakers_detected = {
            seg.get("speaker", "UNKNOWN") for seg in result["segments"]
        }
        print(f"  Speakers detected: {len(speakers_detected)} ({sorted(speakers_detected)})")
        print(f"  -> {diarized_path.name}")
        if not args.keep_audio:
            move_to_done(audio_path, input_dir)
        print()

    print("Done.")


if __name__ == "__main__":
    main()
