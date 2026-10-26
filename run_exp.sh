#!/usr/bin/env bash
set -euo pipefail

: "${ASTRA_API_KEY:?Set ASTRA_API_KEY in your environment}"
: "${OPENAI_API_KEY:?Set OPENAI_API_KEY in your environment}"
: "${YUNWU_API_KEY:?Set YUNWU_API_KEY in your environment}"
export ASTRA_API_KEY OPENAI_API_KEY YUNWU_API_KEY

bash run_codex2.sh
