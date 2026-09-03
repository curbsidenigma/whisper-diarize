# Whisper Diarize

Transcribe and diarize interviews and meetings on your own GPU, with no audio
leaving your machine. Built on [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
for transcription and [WhisperX](https://github.com/m-bain/whisperX) for
word-level alignment and speaker diarization.

Tuned to fit `large-v3` into 8 GB of VRAM, so it runs on a laptop GPU. A 40-minute
recording takes roughly 10-15 minutes end to end with diarization.

Optionally, it ships a [Claude Code](https://claude.com/claude-code) agent that
interviews you about the recording, writes a tailored Whisper prompt, and runs
the pipeline for you — but every step works as a plain CLI without it.

## Requirements

- **NVIDIA GPU**, 6 GB VRAM or more (developed on an RTX 4070 Laptop, 8 GB)
- **Linux or WSL2** with a working NVIDIA driver — check with `nvidia-smi`
- **Python 3.10-3.12** (developed on 3.12)
- **ffmpeg** — `sudo apt install ffmpeg`

CPU-only machines are not supported; both scripts request `device="cuda"`.

## Setup

```bash
git clone <this-repo> whisper-diarize && cd whisper-diarize
python3 -m venv .venv
source .venv/bin/activate
```

Install PyTorch **first**, from the CUDA index. A plain `pip install torch` gets
you the CPU-only build and nothing will run on the GPU:

```bash
pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
pip install -r requirements.txt
```

If your driver is older than CUDA 12.8, swap `cu128` for a build it supports
(`cu121`, `cu124`) and adjust the `nvidia-cublas-cu12` / `nvidia-cudnn-cu12` pins
in [requirements.txt](requirements.txt) to match.

### Every session

```bash
source activate-env.sh
```

This activates the venv and points `LD_LIBRARY_PATH` at the cuBLAS and cuDNN
libraries bundled inside it. **CTranslate2 will not start without it** — the
symptom is `Unable to load libcudnn_ops.so` or a libcublas error at model load.
Note the `source`: the script edits your current shell.

### Hugging Face token (diarization only)

Plain transcription needs nothing. Diarization uses gated pyannote models:

1. Create a read token at https://huggingface.co/settings/tokens
2. Accept the terms at https://huggingface.co/pyannote/speaker-diarization-community-1
3. Export it: `export HF_TOKEN=hf_...` (add it to `~/.bashrc` to persist)

## Quickstart

With setup done, the shortest path from a recording to a transcript:

```bash
source activate-env.sh              # once per shell
cp ~/Downloads/meeting.mp4 input/   # any supported audio or video file
python scripts/transcribe.py input output --language en
```

That writes `output/meeting.txt` and moves the recording to `input/done/`.
Everything below is refinement: `--prompt` to raise accuracy on names and
jargon, `transcribe_diarize.py` to label who said what.

## Usage

Drop audio into `input/` — `.m4a`, `.mp3`, `.wav`, `.flac`, `.ogg`, `.opus`,
`.aac`, `.mp4` are all accepted. Both scripts process every audio file in the
folder and write one file per recording.

**Language defaults to Spanish (`es`).** Pass `--language en` (or any Whisper
language code) for anything else.

After a file transcribes successfully it moves to `input/done/` under its
original name, so re-running the script never reprocesses the same recording.
Pass `--keep-audio` to leave it where it is.

### Plain transcription → `output/<stem>.txt`

```bash
python scripts/transcribe.py input output --language en \
  --prompt "$(cat prompts/examples/interview-en.txt)"
```

### Transcription + diarization → `output/<stem>_speakers.txt`

```bash
python scripts/transcribe_diarize.py input output --language en \
  --speakers 3 --compute-type int8_float16 --batch-size 4 \
  --prompt "$(cat prompts/examples/meeting-en.txt)"
```

Use `--speakers N` when you know the count exactly; otherwise bracket it with
`--min-speakers 2 --max-speakers 5`. Guessing high tends to split one person
across two labels, so prefer a range over a wrong exact number.

### Map `SPEAKER_00` to real names (interactive)

```bash
python scripts/rename_speakers.py output
```

Shows a few sample lines per speaker so you can tell who is who, prompts for each
name, then prints the mapping and asks you to confirm before writing — renaming
in place is not reversible. Pass `--no-in-place` to write a `_renamed.txt` copy
instead. Diarization labels are assigned independently per file, so `SPEAKER_00`
in one recording is unrelated to `SPEAKER_00` in another.

### The `--prompt` flag is worth using

It primes Whisper's vocabulary with names, acronyms, and jargon from your
recording, and it is the cheapest accuracy improvement available on
domain-specific audio. See [prompts/README.md](prompts/README.md) for how to
write one; the prompt must be in the same language as the audio.

## With Claude Code (optional)

```bash
claude
```

then `/transcribe`. The `interview-transcriber` agent asks what the recording is
about, its language, how many speakers, and whether you want diarization; builds
the prompt; runs the pipeline; and helps map speaker labels to names.

## Choosing settings for your GPU

| VRAM     | Model      | `--compute-type` | `--batch-size` |
| -------- | ---------- | ---------------- | -------------- |
| 6-8 GB   | `large-v3` | `int8_float16`   | 4              |
| 10-12 GB | `large-v3` | `float16`        | 8              |
| 16 GB+   | `large-v3` | `float16`        | 16             |

`int8_float16` costs very little accuracy and is what makes `large-v3` fit in
8 GB (~3 GB for the ASR model). Drop to `--model medium` if you are tighter still.

## Layout

```
scripts/
  transcribe.py            # plain transcription
  transcribe_diarize.py    # transcription + alignment + diarization
  rename_speakers.py       # map SPEAKER_XX to real names
prompts/                   # your working prompts (gitignored)
  examples/                # generic templates, safe to share
input/                     # audio waiting to be processed (gitignored)
input/done/                # audio already processed
output/                    # transcripts (gitignored)
activate-env.sh            # venv + CUDA library paths
AGENTS.md                  # instructions for AI coding agents (CLAUDE.md → this)
.claude/                   # optional Claude Code agent, command, permissions
```

`input/`, `output/`, and `prompts/*.txt` are gitignored by design — recordings,
transcripts, and prompts all tend to contain names and other details you would
not want to publish by accident.

## Troubleshooting

**`Unable to load libcudnn_ops.so` / libcublas error** — you did not
`source activate-env.sh` in this shell.

**CUDA out of memory** — a previous run may still hold VRAM. Check with
`nvidia-smi`, and if a stale process is holding it, `pkill -9 python`. Then lower
`--batch-size` to 2 or 1, or switch to `--compute-type int8_float16`.

**`Could not download ... pyannote`** — `HF_TOKEN` is unset, or you have not
accepted the model terms. Both steps are required.

**`ffmpeg: No such file or directory` on a file that clearly exists** — the
filename contains non-ASCII characters (accents, `ñ`). Stage it under an
ASCII-safe symlink and point the script at that:

```bash
mkdir -p /tmp/audio && ln -sf "$PWD/input/entrevista-año.m4a" /tmp/audio/interview.m4a
python scripts/transcribe.py /tmp/audio output --keep-audio
```

`--keep-audio` matters here: without it the script moves the *symlink* into
`/tmp/audio/done/` and the real recording stays in `input/`, so move it to
`input/done/` yourself once the transcript looks right.

**Transcript repeats a phrase forever** — Whisper hallucinating on silence.
`transcribe.py` enables a VAD filter for this; if it persists, trim the silent
stretch from the audio.

## A note on what you record

Transcripts of real conversations are personal data. Everything here runs
locally, but the outputs still name people and repeat what they said — check
what consent and retention rules apply to you before recording, and before
sharing a transcript onward.

## Contributing

Bug reports and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md)
for setup, scope, and how changes get verified without a CI-friendly test suite.
If you are pointing an AI coding agent at this repo, [AGENTS.md](AGENTS.md) is
written for it.

One rule worth repeating: never attach a transcript, a recording, or a working
prompt to an issue or a PR.

## License

MIT — see [LICENSE](LICENSE).
