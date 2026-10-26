#!/usr/bin/env bash
set -euo pipefail

: "${OPENAI_API_KEY:?Set OPENAI_API_KEY before running this script}"

# python -m eval.run_main \
#   --model Qwen3.5-122B-SecAgent \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env OPENAI_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category model_misbehavior \
#   --interactive \
#   --max-user-turns 5 \
#   --user-agent-model claude-sonnet-4-6 \
#   --user-agent-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --user-agent-api-key-env ASTRA_API_KEY \
#   --workers 3

python -m eval.run_main \
  --model Qwen3.8-27B-SecAgent-A100-2 \
  --base-url http://astra.woa.com/astra-llm/v1 \
  --api-key-env OPENAI_API_KEY \
  --judge-mode all \
  --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
  --judge-api-key-env ASTRA_API_KEY \
  --judge-model claude-sonnet-4-6 \
  --category model_misbehavior \
  --interactive \
  --max-user-turns 5 \
  --user-agent-model claude-sonnet-4-6 \
  --user-agent-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
  --user-agent-api-key-env ASTRA_API_KEY \
  --workers 3


# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url https://api.openlux.ai/v1 \
#   --judge-api-key-env OPENAI_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category model_misbehavior \
#   --workers 10

# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url https://api.openlux.ai/v1 \
#   --judge-api-key-env OPENAI_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category user_attack \
#   --workers 10

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
  # --base-url http://astra.woa.com/astra-llm/v1 \
  # --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url https://api.openlux.ai/v1 \
#   --judge-api-key-env OPENAI_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 10


# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env OPENAI_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 1 \
#   --limit 1


# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env OPENAI_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 1


# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env OPENAI_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 1


# ############################################

# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#  --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env OPENAI_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 1


# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env OPENAI_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 1

# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env OPENAI_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 1