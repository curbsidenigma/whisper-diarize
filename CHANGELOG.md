# Changelog

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [0.1.0] - 2026-09-03

First working release. Transcribes and diarizes interviews and meetings entirely
on a local GPU.

### Added

- `scripts/transcribe.py` — plain transcription with faster-whisper, writing one
  `.txt` per recording. VAD filtering is on by default to curb hallucination on
  silence.
- `scripts/transcribe_diarize.py` — transcription, word-level alignment, and
  pyannote speaker diarization via WhisperX, writing one `_speakers.txt` per
  recording with turns grouped by consecutive speaker.
- `scripts/rename_speakers.py` — interactive mapping of `SPEAKER_XX` labels to
  real names, showing sample turns per speaker and confirming the mapping before
  it writes.
- `--keep-audio` on both transcribe scripts. By default a recording moves to
  `input/done/` after a successful run, so re-running never reprocesses it.
- `activate-env.sh` — activates the venv and points `LD_LIBRARY_PATH` at the
  cuBLAS and cuDNN libraries bundled inside it, derived from the venv rather than
  hardcoded, so it works from any checkout location.
- An optional Claude Code agent (`/transcribe`) that asks about the recording,
  writes a tailored Whisper prompt, and runs the pipeline.
- Example prompts in `prompts/examples/` for interviews and meetings, in English
  and Spanish.

### Notes

- Requires an NVIDIA GPU. Tuned so `large-v3` fits in 8 GB of VRAM with
  `--compute-type int8_float16 --batch-size 4`.
- Diarization needs an `HF_TOKEN` and acceptance of the gated pyannote model
  terms. Plain transcription needs neither.
- `input/`, `output/`, and `prompts/*.txt` are gitignored by design: recordings,
  transcripts, and working prompts contain personal data and are never committed.

[Unreleased]: https://github.com/curbsidenigma/whisper-diarize/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/curbsidenigma/whisper-diarize/releases/tag/v0.1.0
