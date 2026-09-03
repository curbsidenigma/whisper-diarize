# AGENTS.md

Instructions for AI coding agents working in this repository. Human contributors
should read [CONTRIBUTING.md](CONTRIBUTING.md) — it covers the same ground with
more context.

`CLAUDE.md` is a symlink to this file, so Claude Code, and any other tool that
reads `AGENTS.md`, share one set of instructions with no drift.

## What this project is

`whisper-diarize` is a local GPU pipeline for transcribing and diarizing interviews and meetings:
faster-whisper for transcription, WhisperX for word-level alignment and pyannote
diarization. No audio leaves the machine. See [README.md](README.md) for setup.

## The rule that matters most

**Never commit recordings, transcripts, or working prompts.** `input/`,
`output/`, and `prompts/*.txt` are gitignored for this reason. They contain real
names, employers, and private conversations.

Concretely:

- Do not `git add -f` anything under those paths, and do not weaken
  [.gitignore](.gitignore) to make something commit.
- Do not paste transcript or prompt content into commit messages, PR
  descriptions, issues, or code comments.
- Anything added to `prompts/examples/` is published. Use fictional
  organizations and fictional names there, always.
- If you need sample data for a test, invent it. Do not reach into `output/`.

## Environment

Every shell needs the venv **and** the CUDA library paths:

```bash
source activate-env.sh
```

Without it, CTranslate2 fails at model load with `Unable to load libcudnn_ops.so`
or a libcublas error. `activate-env.sh` derives the paths from the venv, so it
works from any checkout location — do not hardcode absolute paths anywhere.

`HF_TOKEN` is only needed for diarization. Read it from the environment; never
write a token into a file in the repo.

## Running the pipeline

```bash
# plain            → output/<stem>.txt
python scripts/transcribe.py input output --language en --prompt "..."

# with diarization → output/<stem>_speakers.txt
python scripts/transcribe_diarize.py input output --language en \
  --speakers 3 --compute-type int8_float16 --batch-size 4 --prompt "..."

# map SPEAKER_XX to names (interactive)
python scripts/rename_speakers.py output
```

On 8 GB of VRAM, always use `--compute-type int8_float16 --batch-size 4`.

## Conventions

- **One output file per run.** Plain mode writes `.txt`, diarized mode writes
  `_speakers.txt`. No `.srt`, no redundant second file. This is deliberate —
  do not add extra output formats without being asked.
- **Audio filenames**: `YYYYMMDD-HHMM_desc-<description>.<ext>`. After a
  successful run both scripts move the audio to `input/done/`, keeping its
  original name; `--keep-audio` opts out.
- **Whisper prompts** go in the same language as the audio and stay under
  ~224 tokens — Whisper silently truncates past that. See
  [prompts/README.md](prompts/README.md).
- **Language defaults to `es`** in both scripts. Pass `--language` explicitly
  rather than changing the default.
- **Non-ASCII filenames** can break ffmpeg. Stage the audio behind an ASCII
  symlink in `/tmp/` and keep the original name in `input/`.
- **Speaker labels are per-file.** pyannote assigns `SPEAKER_00` independently
  for each recording; a mapping from one file does not transfer to another.
- **English** for code, comments, docs, commit messages, and CLI output.
  Transcripts and prompts follow the audio's language.
- Dependencies are pinned in [requirements.txt](requirements.txt). If you change
  a version, say why in the commit message.

## Commits

- Follow Conventional Commits: `<type>(<optional scope>): <description>`.
- Types: `feat`, `fix`, `refactor`, `perf`, `style`, `test`, `docs`, `build`,
  `ops`, `chore`.
- Subject: short, imperative, lowercase, no trailing period. The initial commit
  is `chore: init`.
- The body is optional and explains only what the diff does not make obvious.
  Use bullets, give the reasoning, and wrap lines at 72 characters.
- Keep messages brief and precise — only the context needed to understand the
  decision, no filler.
- For a breaking change, add `!` before the `:` and a `BREAKING CHANGE:
  <description>` footer.
- Make the change, propose the message, and wait for the user's explicit
  approval before committing. Never `push` without an explicit request.

## Before you finish

- `python scripts/<changed>.py --help` still works.
- Nothing under `input/`, `output/`, or `prompts/*.txt` is staged —
  `git status --short` should show none of it.
- No absolute paths, usernames, or tokens added anywhere.
- New user-facing flags or behavior are reflected in [README.md](README.md).
