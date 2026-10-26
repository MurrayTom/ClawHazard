#!/usr/bin/env bash
set -euo pipefail

: "${OPENAI_API_KEY:?Set OPENAI_API_KEY before running this script}"

python -m eval.run_main \
  --model Qwen3.8-27B-SecAgent-A100-2 \
  --base-url http://astra.woa.com/astra-llm/v1 \
  --api-key-env ASTRA_API_KEY \
  --judge-mode all \
  --judge-base-url https://api.openlux.ai/v1 \
  --judge-api-key-env OPENAI_API_KEY \
  --judge-model claude-sonnet-4-6 \
  --category model_misbehavior \
  --skill-prompt-mode tools_only \
  --workers 10
python -m eval.run_main \
  --model Qwen3.8-27B-SecAgent-A100-2 \
  --base-url http://astra.woa.com/astra-llm/v1 \
  --api-key-env ASTRA_API_KEY \
  --judge-mode all \
  --judge-base-url https://api.openlux.ai/v1 \
  --judge-api-key-env OPENAI_API_KEY \
  --judge-model claude-sonnet-4-6 \
  --category user_attack \
  --skill-prompt-mode tools_only \
  --workers 10

# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url https://api.openlux.ai/v1 \
#   --judge-api-key-env OPENAI_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 10

# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url https://api.openlux.ai/v1 \
#   --judge-api-key-env OPENAI_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 10

# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url https://api.openlux.ai/v1 \
#   --judge-api-key-env OPENAI_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 10