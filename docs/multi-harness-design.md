# Claw-Bias 多 Harness 对比评测设计方案

> 目标：在同一套攻击用例上对比不同 Agent Harness 的安全/实用性表现  
> 原则：**不改现有 FC loop（task_agent.py）的任何代码**，仅新增 harness 适配层  
> 日期：2026-10-10

---

## 1. 研究动机

| Harness | 代表什么 |
|---|---|
| FC Loop（现状） | 模型内生 agent 安全能力——模型自己决定调不调工具、怎么调 |
| Codex | "模型 + Codex 框架"组合的安全能力——harness 有额外的 sandbox/policy/reasoning |
| OpenClaw | "模型 + OpenClaw 框架"组合的安全能力——harness 有 skill 加载、exec 编排等机制 |

三者的差异 = harness 框架带来的安全增量（或新攻击面）。

---

## 2. 架构总览

```
                    ┌─────────────────────┐
                    │     run_main.py      │
                    │  --harness fc|codex  │
                    │         |openclaw    │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌───────────┐  ┌───────────┐  ┌──────────────┐
        │ TaskAgent  │  │CodexAgent │  │OpenClawAgent │
        │ (FC Loop)  │  │           │  │              │
        │  现有不动   │  │  新增      │  │  新增         │
        └─────┬─────┘  └─────┬─────┘  └──────┬───────┘
              │               │               │
              │  structured   │  exec         │  exec
              │  function     │  mcporter     │  mcporter
              │  calling      │  call ...     │  call ...
              │               │               │
              └───────────────┼───────────────┘
                              ▼
                    ┌─────────────────────┐
                    │    Mock Service      │
                    │  (HTTP + /audit)     │
                    └─────────┬───────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  EnvironmentRecord            │
              │  (audit_calls + state diff)   │
              └───────────────┬───────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        SafetyEval     TaskSuccessEval    LLM Judge
           (全部不动，消费统一的 EnvironmentRecord)
```

---

## 3. 四个核心设计点

### 3.1 工具能力对齐

**结论：天然对齐，无需额外适配层。**

三种 harness 都使用同一份 SKILL.md 作为工具描述来源：

| Harness | 工具描述 | 调用方式 | 底层 |
|---|---|---|---|
| FC Loop | SKILL.md 作为 system prompt + OpenAPI → function tool schema | 结构化 JSON function call | `environment.execute()` → HTTP |
| Codex | SKILL.md 放 workspace，agent 自行阅读 | exec `mcporter call ...` | mcporter → HTTP |
| OpenClaw | SKILL.md 放 workspace，agent 自行阅读 | exec `mcporter call ...` | mcporter → HTTP |

- FC Loop 走的是自己独有的结构化路径（`openapi_converter.py` → function schema），**不改**
- Codex / OpenClaw 走的是 SKILL.md 里写的 `mcporter call` CLI 命令，**不需要 CLI wrapper**——它们拿到 SKILL.md 自己就会 exec
- 调用方式的差异属于 harness 特性，是要对比的自变量，不需要消除
- 三者最终都打到同一个 Mock Service 的同一批 HTTP 端点

**唯一要处理的：端口号动态化。** SKILL.md 模板里硬编码的是 `http://127.0.0.1:39200`，但 Mock Service 实际端口可能不同（`--port 0` 随机分配 / 并发时多 case 各不同）。

解决方式——setup 阶段渲染 SKILL.md：

```python
def prepare_skill_text(skill_text: str, actual_port: int) -> str:
    """替换 SKILL.md 中的默认端口为 Mock Service 实际端口"""
    return skill_text.replace(
        "http://127.0.0.1:39200",
        f"http://127.0.0.1:{actual_port}"
    )
```

在 `codex_agent.py` / `openclaw_agent.py` 的 `run()` 开头调用，写入 sandbox workspace 的 SKILL.md 是正确端口的版本。FC loop 不受影响——它不读 SKILL.md 里的端口。

### 3.2 审计证据统一

**结论：全部从 Mock Service `/audit` 端点采集，下游 evaluator 零改动。**

现有审计数据的三个消费者：

| 消费者 | 用什么 | 做什么 |
|---|---|---|
| **SafetyEvaluator** | `audit_calls` 里的 operation + params + succeeded | 判断攻击目标操作是否被成功调用 |
| **TaskSuccessEvaluator** | `audit_calls`（required/forbidden calls）+ `state_before/after` | 判断用户正常任务是否完成 |
| **LLM Judge** | `audit_calls` + `state_changes` + `final_output` | 作为 evidence 给 judge 模型打分 |

三者消费的都是 `EnvironmentRecord`：

```python
@dataclass
class EnvironmentRecord:
    base_url: str
    state_before: dict    # Mock Service 启动后的初始快照
    state_after: dict     # agent 执行完毕后的终态快照
    audit_calls: list[dict]  # 每条: {endpoint, method, request_body, response_body}
```

不管 agent 怎么调用（function call / mcporter exec / curl），请求最终都到 Mock Service 的 HTTP 端点，服务侧 audit log 格式天然一致。

Codex / OpenClaw 的采集方式：

```python
# agent 跑完后
audit = request_json(f"{base_url}/{family}/audit")
state_after = get_environment_snapshot(base_url)

environment_record = EnvironmentRecord(
    base_url=base_url,
    state_before=state_before,
    state_after=state_after,
    audit_calls=audit["calls"],  # 与 FC loop 格式完全一致
)
```

### 3.3 Workspace 隔离

**目标：防止 Codex / OpenClaw 读到评测元数据（meta.yaml、grading targets、evaluator 代码）。**

构造干净的 sandbox workspace：

```
sandbox_workspace/
├── SKILL.md                  # 端口已渲染的 skill 描述
├── external_files/           # case 里需要的用户可见数据文件（如有）
└── data/                     # 其他用户可见材料（如有）
```

**不放进 sandbox 的：**

| 文件 | 原因 |
|---|---|
| `meta.yaml` | 包含攻击意图、target_operation、target_entity |
| `source_report.json` | 包含评分标准和 check_items |
| `state_before.json` | 包含预期初始状态 |
| `run_manifest.json` | 包含环境配置和进程信息 |
| `eval/` 目录 | evaluator、judge、聚合逻辑等全部代码 |
| `tasks_filtered*/` | 所有 case 定义 |

实现：

```python
sandbox = tempfile.mkdtemp(prefix="claw-bias-sandbox-")
# 只放 skill 文件和用户可见材料
write_rendered_skill(Path(sandbox) / "SKILL.md", skill_text, actual_port)
copy_external_files(skill_dir / "external_files", Path(sandbox) / "external_files")
# harness 的 cwd 设为 sandbox
```

- Codex：`--cwd sandbox`
- OpenClaw：spawn isolated session 时指定 workspace 目录

### 3.4 预算和停止条件

**统一预算协议：**

```python
@dataclass(frozen=True)
class AgentBudget:
    max_tool_calls: int = 12     # 工具调用上限
    max_llm_turns: int = 20      # LLM 交互轮次上限
    timeout_seconds: int = 300   # 绝对超时
```

各 harness 的映射：

| 预算维度 | FC Loop | Codex | OpenClaw |
|---|---|---|---|
| `max_tool_calls` | 现有 `steps` 计数 | Mock Service 侧限制 | Mock Service 侧限制 |
| `max_llm_turns` | 隐含在 loop 里 | timeout 兜底 | timeout 兜底 |
| `timeout_seconds` | 不需要（同步 loop） | 进程超时 kill | session timeout |

**Mock Service 侧硬限制（最可靠的兜底）：**

当调用数达到上限时，Mock Service 直接返回错误，不依赖 harness 侧计数：

```python
# Mock Service 中间件
if len(audit_log) >= max_tool_calls:
    return {"success": False, "error": "Tool call budget exhausted"}, 429
```

**统一停止原因枚举：**

```python
stop_reason: Literal["finished", "max_tool_calls", "max_turns", "timeout", "error"]
```

---

## 4. 数据模型扩展

`AgentRun` 新增两个字段（不影响现有字段）：

```python
@dataclass
class AgentRun:
    messages: list[dict]              # harness 原生格式，debug / 可追溯
    normalized_messages: list[dict]   # 统一 OpenAI 格式，judge 用（FC loop 可直接复用 messages）
    final_output: str
    tool_executions: list[ToolExecution]
    stop_reason: str
    steps: int
    harness: str                      # "fc_loop" | "codex" | "openclaw"
```

---

## 5. 改动清单

### 新增文件

```
eval/agent/
├── base.py                      # AgentHarness protocol + AgentBudget 定义
├── codex_agent.py               # Codex harness 适配：启动 → 等完成 → 采集证据
└── openclaw_agent.py            # OpenClaw harness 适配：同上
```

### 小改文件

```
eval/agent/task_agent.py         # 实现 AgentHarness protocol，接受 AgentBudget（行为不变）
eval/models.py                   # AgentRun 加 harness / normalized_messages 字段
eval/run_main.py                 # 加 --harness fc|codex|openclaw 参数，按选择实例化 agent
```

### 不动的文件

```
eval/environment/*               # 全部不动
eval/evaluators/*                # 全部不动（SafetyEvaluator、TaskSuccessEvaluator、LLM Judge）
eval/cases/*                     # 全部不动
eval/run_refusal.py              # 不动
eval/run_clarification.py        # 不动
lab_setup.py                     # 不动
mock_service_utils.py            # 不动
所有 Mock Service (server.py)     # 不动
所有 SKILL.md 模板                # 不动（端口渲染在 agent 层做）
```

---

## 6. 执行入口

```bash
# 现有方式，完全不变
python -m eval.run_main --model MODEL --harness fc --category injection --workers 4

# Codex harness
python -m eval.run_main --model MODEL --harness codex --category injection --workers 4

# OpenClaw harness
python -m eval.run_main --model MODEL --harness openclaw --category injection --workers 4
```

三次跑完后，结果文件格式一致，可直接横向对比 `summary.safety` / `summary.utility`。
