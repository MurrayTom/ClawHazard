#!/usr/bin/env python3
"""
测试各代理 + 各模型的 Responses API 支持情况。
用法: python scripts/test_responses_api.py
需要环境变量: VENUS_API_KEY, ASTRA_API_KEY, YUNWU_API_KEY
"""

import os
import sys
import traceback
from openai import OpenAI


# ── 代理配置 ──────────────────────────────────────────
PROVIDERS = {
    "venus": {
        "base_url": "https://v2.open.venus.woa.com/llmproxy/v1",
        "api_key_env": "VENUS_API_KEY",
    },
    "astra": {
        "base_url": "http://astra.woa.com/astra-llm/v1",
        "api_key_env": "ASTRA_API_KEY",
    },
    "yunwu": {
        "base_url": "https://api.openlux.ai/v1",
        "api_key_env": "YUNWU_API_KEY",
    },
}

# ── 要测试的 (代理, 模型) 组合 ─────────────────────────
TEST_COMBOS = [
    # venus
    ("venus", "gpt-5.4"),
    ("venus", "claude-sonnet-4-6"),
    ("venus", "deepseek-v4-flash"),
    ("venus", "glm-5.2-external"),
    # astra
    ("astra", "Qwen3.5-122B-SecAgent"),
    ("astra", "DSV4-Flash-SecAgent"),
    # yunwu
    ("yunwu", "claude-sonnet-4-6"),
]


def test_responses_basic(client: OpenAI, model: str) -> dict:
    """测试 1: 最基础的 responses.create，纯文本，无工具"""
    resp = client.responses.create(
        model=model,
        input="请回复'hello'，不要说其他内容。",
    )
    return {
        "status": "ok",
        "output": resp.output_text[:200] if hasattr(resp, "output_text") else str(resp.output)[:200],
    }


def test_responses_function_tool(client: OpenAI, model: str) -> dict:
    """测试 2: responses.create + function tool"""
    resp = client.responses.create(
        model=model,
        input="查询北京的天气。",
        tools=[
            {
                "type": "function",
                "name": "get_weather",
                "description": "查询指定城市的天气",
                "parameters": {
                    "type": "object",
                    "properties": {"city": {"type": "string", "description": "城市名"}},
                    "required": ["city"],
                    "additionalProperties": False,
                },
            }
        ],
    )
    output = resp.output if hasattr(resp, "output") else str(resp)
    return {
        "status": "ok",
        "output": str(output)[:300],
    }


def test_responses_streaming(client: OpenAI, model: str) -> dict:
    """测试 3: responses.create 流式输出"""
    chunks = []
    stream = client.responses.create(
        model=model,
        input="说一个数字。",
        stream=True,
    )
    for event in stream:
        chunks.append(type(event).__name__)
        if len(chunks) >= 10:
            break
    return {
        "status": "ok",
        "chunks": len(chunks),
        "event_types": list(set(chunks)),
    }


# ── 主逻辑 ────────────────────────────────────────────
TESTS = [
    ("basic", test_responses_basic),
    ("function_tool", test_responses_function_tool),
    ("streaming", test_responses_streaming),
]


def main():
    # 从 OpenClaw config 补充环境变量
    try:
        import json
        cfg = json.load(open("/projects/.openclaw/openclaw.json"))
        providers = cfg.get("models", {}).get("providers", {})
        env_map = {"venus": "VENUS_API_KEY", "astra": "ASTRA_API_KEY", "yunwu": "YUNWU_API_KEY"}
        for prov, env_var in env_map.items():
            if not os.environ.get(env_var):
                key = providers.get(prov, {}).get("apiKey", "")
                if key:
                    os.environ[env_var] = key
    except Exception:
        pass

    results = []

    for provider_name, model in TEST_COMBOS:
        prov = PROVIDERS[provider_name]
        api_key = os.environ.get(prov["api_key_env"], "")
        if not api_key:
            print(f"\n⏭️  [{provider_name}/{model}] 跳过 - {prov['api_key_env']} 未设置")
            continue

        client = OpenAI(api_key=api_key, base_url=prov["base_url"])

        print(f"\n{'='*60}")
        print(f"🔍 {provider_name}/{model}")
        print(f"   base_url: {prov['base_url']}")
        print(f"{'='*60}")

        for test_name, test_fn in TESTS:
            try:
                result = test_fn(client, model)
                status = "✅"
                detail = result.get("output", result.get("chunks", ""))
                print(f"  {status} {test_name}: {str(detail)[:120]}")
                results.append((provider_name, model, test_name, "ok", ""))
            except Exception as e:
                status = "❌"
                err_msg = str(e)
                # 提取关键错误信息
                short_err = err_msg[:200]
                if "503" in err_msg:
                    short_err = "503 - Responses API not supported for this model"
                elif "498" in err_msg:
                    short_err = "498 - upstream service down (Responses API not supported)"
                elif "404" in err_msg:
                    short_err = "404 - endpoint not found"
                elif "401" in err_msg or "403" in err_msg:
                    short_err = f"{err_msg[:50]} - auth error"
                print(f"  {status} {test_name}: {short_err}")
                results.append((provider_name, model, test_name, "fail", short_err))
                # 如果 basic 就挂了，后面不用测了
                if test_name == "basic":
                    for remaining_test, _ in TESTS[1:]:
                        print(f"  ⏭️  {remaining_test}: skipped (basic failed)")
                        results.append((provider_name, model, remaining_test, "skip", ""))
                    break

    # ── 汇总 ──
    print(f"\n\n{'='*60}")
    print("📊 汇总")
    print(f"{'='*60}")
    print(f"{'Provider':<10} {'Model':<30} {'Basic':>8} {'FuncTool':>10} {'Stream':>8}")
    print("-" * 70)

    combo_results = {}
    for prov, model, test, status, err in results:
        key = (prov, model)
        if key not in combo_results:
            combo_results[key] = {}
        combo_results[key][test] = status

    for (prov, model), tests in combo_results.items():
        def sym(s):
            return {"ok": "✅", "fail": "❌", "skip": "⏭️"}.get(s, "?")
        print(f"{prov:<10} {model:<30} {sym(tests.get('basic','')):>8} {sym(tests.get('function_tool','')):>10} {sym(tests.get('streaming','')):>8}")


if __name__ == "__main__":
    main()
