# Contributing

Thanks for taking a look. This is a small, focused project — a local GPU
transcription and diarization pipeline — and it intends to stay small. The most
useful contributions are bug fixes, GPU/driver compatibility improvements, and
documentation that saves the next person an hour of CUDA debugging.

## Before you open an issue

**Do not paste transcript content, audio, or your working prompts into an issue,
a pull request, or a commit message.** They contain real names and private
conversations. Reduce the problem to a synthetic example, or describe it in
words. This is the one rule we will actually push back on.

A good bug report includes:

- GPU model and VRAM, plus `nvidia-smi` output (driver and CUDA version)
- OS — native Linux or WSL2
- `python -c "import torch; print(torch.__version__, torch.version.cuda)"`
- The exact command you ran, with any prompt text replaced by `"..."`
- The full traceback

Most reported failures turn out to be one of three things: `activate-env.sh` was
not sourced, `HF_TOKEN` is missing or the pyannote terms were not accepted, or a
CPU-only PyTorch build got installed. The
[README troubleshooting section](README.md#troubleshooting) covers all three —
worth a look first.

## Development setup

Follow [Setup in the README](README.md#setup), then for each shell:

```bash
source activate-env.sh
```

## Making a change

1. Fork and branch off `main`.
2. Make the change. Match the surrounding style — these are plain `argparse`
   scripts with docstring usage examples at the top, no framework, no config
   files. Keep it that way.
3. Verify it (below).
4. Update [README.md](README.md) if you changed a flag or user-facing behavior,
   and [AGENTS.md](AGENTS.md) if you changed a project convention.
5. Add yourself to [AUTHORS.md](AUTHORS.md) in the same pull request.
6. Open the PR describing what changed and how you verified it on real audio.

## Verifying a change

There is no automated test suite — the pipeline's real behavior depends on a
GPU, gated model downloads, and multi-gigabyte weights, none of which run in CI.
So verification is manual, and honest reporting of what you actually ran matters
more than usual. At minimum:

```bash
python scripts/transcribe.py --help
python scripts/transcribe_diarize.py --help
python scripts/rename_speakers.py --help
```

Then run the path you touched against a short recording of your own — two or
three minutes with at least two speakers is enough to exercise diarization — and
say so in the PR. If you cannot test on a GPU, open the PR anyway and say that
clearly; it can be tested for you.

If you add anything that *can* be tested without a GPU (timestamp formatting,
the speaker-file parser, filename handling), a small test alongside it is very
welcome.

## Style

- Python 3.10+, standard library plus the pinned dependencies. Prefer adding no
  new dependency; if one is genuinely needed, pin it in
  [requirements.txt](requirements.txt) and say why.
- English for code, comments, docs, commit messages, and CLI output.
- Comment the non-obvious — a VRAM constraint, a workaround for an upstream bug —
  not the obvious.
- Commit messages follow
  [Conventional Commits](https://www.conventionalcommits.org) —
  `<type>(<optional scope>): <description>`, with a short, imperative,
  lowercase subject and no trailing period — for example
  `fix(diarize): keep speaker mapping stable across batched files`. Types are
  `feat`, `fix`, `refactor`, `perf`, `style`, `test`, `docs`, `build`, `ops`
  and `chore`. Add a body, wrapped at 72 characters, explaining *why* when it
  is not self-evident, and mark a breaking change with `!` before the `:` plus
  a `BREAKING CHANGE:` footer. [AGENTS.md](AGENTS.md) has the full rules.

## Scope

Likely to be merged: bug fixes, compatibility with other GPUs and CUDA versions,
clearer errors, documentation, small quality-of-life flags.

Likely to be declined: extra output formats (the one-file-per-run rule in
[AGENTS.md](AGENTS.md) is deliberate), cloud transcription backends (the point is
that audio never leaves your machine), web UIs, and large refactors that turn
three readable scripts into a framework. If you are planning something big, open
an issue first so neither of us wastes the effort.

## Conduct

Be decent to other people in issues and reviews. Assume good faith, critique the
change and not the person. Behavior that makes this an unpleasant place to
contribute gets you asked to leave.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE) that covers this project.
