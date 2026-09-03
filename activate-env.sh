#!/usr/bin/env bash
# Activate the virtualenv and point CTranslate2 at the cuBLAS/cuDNN libraries
# that ship inside it. Without this, faster-whisper fails at load time with
# "Unable to load libcudnn_ops.so" or a libcublas error.
#
# Usage:  source activate-env.sh
#
# Note the `source` — this script edits your current shell's environment,
# so running it as ./activate-env.sh has no effect.

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$REPO_DIR/.venv" ]; then
    echo "No .venv found in $REPO_DIR — see README.md for setup." >&2
    return 1 2>/dev/null || exit 1
fi

source "$REPO_DIR/.venv/bin/activate"

SITE_PACKAGES="$(python -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
export LD_LIBRARY_PATH="$SITE_PACKAGES/nvidia/cublas/lib:$SITE_PACKAGES/nvidia/cudnn/lib:$LD_LIBRARY_PATH"

if [ -z "$HF_TOKEN" ]; then
    echo "Warning: HF_TOKEN is not set. Plain transcription works, diarization will not."
    echo "  Get a token at https://huggingface.co/settings/tokens"
fi
