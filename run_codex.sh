#!/usr/bin/env bash
set -euo pipefail

: "${OPENAI_API_KEY:?Set OPENAI_API_KEY before running this script}"


# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/gpt-5.4 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category user_attack \
#   --workers 1

python3 -m eval.run_main \
  --harness codex \
  --model venus/glm-5.2-external \
  --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
  --api-key-env ASTRA_API_KEY \
  --judge-mode all \
  --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
  --judge-api-key-env ASTRA_API_KEY \
  --judge-model claude-sonnet-4-6 \
  --category user_attack \
  --workers 1


#============================================
# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/gpt-5.4 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 1

# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/gpt-5.4 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 1 

# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/gpt-5.4 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 1 

# # ############################################

# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/glm-5.2-external \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 1

# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/glm-5.2-external \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 1 

# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/glm-5.2-external \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 1 

# # ############################################

# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/claude-sonnet-4-6 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 1 \
#   --limit 1


# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/claude-sonnet-4-6 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 1


# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/claude-sonnet-4-6 \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 1


# ############################################

# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/deepseek-v4-flash \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category injection \
#   --workers 1


# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/deepseek-v4-flash \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category special_strategy \
#   --workers 1 

# python3 -m eval.run_main \
#   --harness codex \
#   --model venus/deepseek-v4-flash \
#   --base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --api-key-env ASTRA_API_KEY \
#   --judge-mode all \
#   --judge-base-url http://v2.open.venus.oa.com/llmproxy/v1 \
#   --judge-api-key-env ASTRA_API_KEY \
#   --judge-model claude-sonnet-4-6 \
#   --category supply_chain \
#   --workers 1