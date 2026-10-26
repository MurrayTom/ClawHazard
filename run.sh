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
#   --category user_attack \
#   --workers 5


python -m eval.run_main \
  --model Qwen3.8-27B-SecAgent-A100-2 \
  --base-url http://astra.woa.com/astra-llm/v1 \
  --api-key-env OPENAI_API_KEY \
  --judge-mode all \
  --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
  --judge-api-key-env ASTRA_API_KEY \
  --judge-model claude-sonnet-4-6 \
  --category user_attack \
  --workers 5

# python -m eval.run_main \
#   --model gpt-5.4-mini \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
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
#   --workers 5 \
#   --limit 5

# python -m eval.run_main \
#   --model Qwen3.8-27B-SecAgent-A100-2 \
#   --base-url http://astra.woa.com/astra-llm/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url https://api.openlux.ai/v1 \
#   --judge-api-key-env OPENAI_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category user_attack \
#   --workers 50




# python -m eval.run_main \
#   --model gpt-5.4 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 5 


# python -m eval.run_main \
#   --model gpt-5.4 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 5 


# python -m eval.run_main \
#   --model gpt-5.4 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 5


# ############################################

# python -m eval.run_main \
#   --model glm-5.2-external \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 1


# python -m eval.run_main \
#   --model glm-5.2-external \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 1


# python -m eval.run_main \
#   --model glm-5.2-external \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 1


# ############################################

# python -m eval.run_main \
#   --model claude-sonnet-4-6 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 1


# python -m eval.run_main \
#   --model claude-sonnet-4-6 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 1


# python -m eval.run_main \
#   --model claude-sonnet-4-6 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 1


# ############################################

# python -m eval.run_main \
#   --model deepseek-v4-flash \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 1


# python -m eval.run_main \
#   --model deepseek-v4-flash \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 1

# python -m eval.run_main \
#   --model deepseek-v4-flash \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 1