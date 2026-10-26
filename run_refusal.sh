python -m eval.run_refusal \
  --model gpt-5.4-mini \
  --base-url https://api.openlux.ai/v1 \
  --api-key-env OPENAI_API_KEY

python -m eval.run_clarification \
  --model gpt-5.4-mini \
  --base-url https://api.openlux.ai/v1 \
  --api-key-env OPENAI_API_KEY