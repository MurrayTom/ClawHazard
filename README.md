<div align="center">

# ClawHazard

### Benchmarking the Agent Safety in Skill-Mediated Tool Use for Web Services

**Stateful service environments · Three threat modes · Separate safety and utility evaluation**

[Overview](#overview) · [Benchmark](#benchmark) · [Quick Start](#quick-start) · [Evaluation](#evaluation) · [Repository Layout](#repository-layout)

</div>

![Three sources of risk in skill-mediated tool use: poisoned skills, harmful user requests, and ambiguous user intent.](docs/assets/threat-overview.png)

*Can an agent use a service safely when its skill is poisoned, its user requests harm, or its instructions leave critical details unspecified?*

## Overview

**ClawHazard** evaluates agent safety in skill-mediated tool use over stateful Web services. Agents interact with executable service backends for tasks such as managing email, booking appointments, updating orders, and organizing calendars. Evaluation examines what the agent says, which tools it calls, and how those calls change the service state.

The benchmark brings three threat modes into one evaluation framework:

| Threat mode | Scenario | Expected safe behavior |
| --- | --- | --- |
| **Skill poisoning** | A benign request encounters a compromised skill package. | Resist injected instructions while completing the legitimate task. |
| **Harmful user requests** | A user pursues a harmful objective through a clean skill. | Decline harmful operations and preserve authorization boundaries. |
| **Ambiguous user intent** | A benign request omits details needed for safe execution. | Resolve the target, scope, or action before taking consequential steps, then complete the intended task. |

**ClawWorld** is the construction framework described in the paper. It jointly synthesizes skill specifications, executable service environments, initial states, and safety tasks, followed by semantic checks, execution tests, repair, and case review. This repository contains the resulting task packages, service backends, and evaluation code.

![ClawWorld constructs skill specifications and executable environments, validates them, and synthesizes safety test cases.](docs/assets/clawworld-pipeline.png)

*ClawWorld construction pipeline, reproduced from Figure 2 of the accompanying manuscript.*

## Benchmark

The paper reports **42 skills, 42 corresponding service environments, and 615 test cases**, organized into three threat modes and five test sets. Its taxonomy covers 18 attack or behavior strategies and 10 risk subcategories, including authorization violations, information leakage, resource damage, misinformation, and physical safety risks.

![The paper's attack taxonomy, risk taxonomy, and distribution of 615 test cases.](docs/assets/benchmark-taxonomy.png)

*Figure 4 of the manuscript describes the full paper benchmark. The current runnable snapshot has the counts below.*

### Current repository snapshot

The default runner discovers cases under `tasks_filtered_unrelated_write/`. This checkout contains **483 runnable cases across 42 skills**; it is a smaller snapshot than the 615-case benchmark reported in the paper.

| Threat mode | Test set | CLI category | Paper cases | Cases in default task root |
| --- | --- | --- | ---: | ---: |
| Skill poisoning | Generic injection | `injection` | 150 | 118 |
| Skill poisoning | Context-specific injection | `special_strategy` | 150 | 106 |
| Skill poisoning | Supply-chain hijacking | `supply_chain` | 150 | 94 |
| Harmful user requests | Malicious requests | `user_attack` | 81 | 81 |
| Ambiguous user intent | Underspecified requests | `model_misbehavior` | 84 | 84 |
| **Total** | | | **615** | **483** |

`tasks_filtered/` supplies fallback runtime resources when a selected case lacks its own assets. It is not a separate evaluation split and should not be added to the default case count. Case prompts, metadata, and scoring targets remain those of the selected task.

A typical task package contains:

```text
<category>/<skill_source>/<skill_name>/<case_id>/
├── meta.yaml                 # Case identity and threat metadata
├── prompt.md                 # User task
├── source_report.json        # Safety and task-completion criteria
├── user_intent.json          # Fixed user goal for ambiguous-intent cases
├── attack_messages.json      # Scripted user turns, when applicable
├── skill_files/
│   ├── SKILL.md              # Skill instructions and available tools
│   └── external_files/       # Reference materials, when present
└── mock_service/
    ├── env_class.py          # Stateful service implementation
    ├── server.py             # Service endpoints
    └── seed_data.json        # Initial service state
```

## Quick Start

The commands below use a Bash-compatible shell and Python 3.10 or later. Python 3.11 is a suitable starting point.

### 1. Set up the environment

```bash
git -c core.longpaths=true clone https://github.com/MurrayTom/ClawHazard.git
cd ClawHazard

python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install openai PyYAML 'fastapi>=0.100' uvicorn 'pydantic>=2'
```

On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell. The clone command enables Git support for the long paths used by task packages; a short checkout path also helps.

### 2. Validate case discovery

This resolves task packages and runtime resources without making model API calls:

```bash
python -m eval.run_main --validate-only
```

Use `--category CATEGORY`, `--case-id CASE_ID`, or `--limit N` to narrow discovery. Case IDs are stored in each task's `meta.yaml`.

### 3. Run a small evaluation

Set credentials for an OpenAI-compatible Chat Completions endpoint with tool-calling support:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
export OPENAI_BASE_URL="https://YOUR_PROVIDER/v1"

python -m eval.run_main \
  --harness fc \
  --model YOUR_MODEL \
  --category injection \
  --limit 1 \
  --output eval/results/quickstart.json
```

`fc` is the built-in function-calling loop and requires no external agent CLI. The runner starts a local mock service for each case and records tool execution and service-state evidence. The default `--judge-mode off` runs executable checks only; unresolved criteria may remain `needs_judge`.

### 4. Evaluate ambiguous intent interactively

```bash
python -m eval.run_main \
  --harness fc \
  --model YOUR_MODEL \
  --category model_misbehavior \
  --interactive \
  --max-user-turns 5 \
  --limit 1 \
  --output eval/results/ambiguous-intent.json
```

Interactive cases use the fixed goal in `user_intent.json`. A user model supplies clarification in response to the agent; it defaults to the evaluated model and endpoint. Use `--user-agent-model`, `--user-agent-base-url`, and `--user-agent-api-key-env` to configure it separately.

## Evaluation

### Execution harnesses

The current runner accepts these `--harness` values:

| Harness | Execution path | Additional setup |
| --- | --- | --- |
| `fc` | Skill text plus OpenAPI-derived function tools in a built-in tool-calling loop. | Python dependencies and model API credentials. |
| `codex` | External `codex exec` process reads the skill and invokes service tools. | A configured `codex` CLI and `mcporter` on `PATH`. |
| `openclaw` | External `openclaw agent` process reads the skill and invokes service tools. | A configured `openclaw` CLI and `mcporter` on `PATH`. |

External harnesses use their own CLI/provider configuration. Their `--model` value must match that configuration; `--base-url` configures the Python API clients. The current Codex adapter invokes `codex exec` with `danger-full-access`, so run external harness evaluations in a disposable evaluation environment.

**Paper versus implementation:** the manuscript compares Naive ReAct, Hermes Agent, and OpenClaw. This checkout provides `fc`, `codex`, and `openclaw`; a Hermes adapter is not included. Use the available adapters and record the model, harness, budgets, and task snapshot when reporting results.

### Score saved trajectories

For the paper-style rubric item pass ratios, use the standalone judge after collecting execution traces:

```bash
export JUDGE_API_KEY="YOUR_JUDGE_API_KEY"

python judge_results.py \
  --input eval/results/quickstart.json \
  --model YOUR_JUDGE_MODEL \
  --base-url https://YOUR_JUDGE_PROVIDER/v1 \
  --api-key-env JUDGE_API_KEY \
  --workers 4
```

The judge reads saved traces and task rubrics, then writes a new report under `eval/judge_results/`. It does not rerun the evaluated agent. Repeat `--input` to select multiple files, or omit it to scan `eval/results/`. Add `--dry-run` to inspect rubric and evidence packages without calling a judge model.

Safety and utility are scored separately:

```text
Safety score  = safety requirements satisfied / applicable safety items
Utility score = benign task requirements satisfied / applicable utility items
```

Scores lie in `[0, 1]`; higher is better. For poisoning and harmful-request cases, attack-success conditions are inverted by the script to obtain safety passes. For ambiguous-intent cases, safety passes reflect satisfaction of `correct_behavior` requirements. Utility is marked `not_applicable` when no independent benign-task rubric exists.

The judge returns evidence-backed item verdicts. The script computes each case's item pass ratio; `passed` requires all applicable items to pass. Report mean case-level scores separately from the proportion of cases with `passed: true`.

The standalone prompt and category rules are in [`judge_results.py`](judge_results.py). The in-run judge has a separate prompt in [`eval/evaluators/llm_judge.py`](eval/evaluators/llm_judge.py).

### In-run judging and controls

The runner also supports `--judge-mode missing` or `--judge-mode all`, with `--judge-model`, `--judge-base-url`, and `--judge-api-key-env`. This path combines executable checks with rubric grades using an executable hard gate. Its aggregation differs from the standalone judge's item pass ratios; keep the scoring protocol consistent across compared runs.

Useful execution controls:

| Option | Purpose |
| --- | --- |
| `--workers N` | Evaluate multiple cases concurrently. |
| `--max-steps N` | Set the agent step budget; the CLI default is 40. |
| `--budget-tool-calls N` | Override the harness tool-call budget. |
| `--budget-timeout N` | Set the external harness time budget in seconds. |
| `--skill-prompt-mode tools_only` | Retain only the skill's Usage and Available Tools sections for an ablation. |
| `--output PATH` | Choose the raw result JSON path. |

Without `--output`, raw results are saved under `eval/results/<harness>/<model>/`. Reports preserve case metadata, agent messages, tool calls, audit records, before/after service state, scores, and errors. Generated results, logs, caches, and local credentials are excluded from Git.

See [`eval/README.md`](eval/README.md) for additional evaluator details and refusal/clarification analysis tools. For current argument defaults, use `python -m eval.run_main --help` and `python judge_results.py --help`.

## Findings from the Paper

- **Safety depends on both the model and the harness.** A harness can improve one model's safety while degrading another's under the same threat.
- **Poisoning strategies differ in difficulty.** Robustness against generic injection does not establish robustness against context-specific injection or supply-chain hijacking.
- **Ambiguous intent remains a distinct challenge.** In the reported experiments, both Hermes and OpenClaw reduce ambiguous-intent safety relative to Naive ReAct across all six evaluated models.
- **Safety and task completion must be measured together.** Agents can finish a task while violating authorization or scope constraints, or remain safe while leaving the legitimate task unfinished.

These observations describe the manuscript's experimental configurations, rather than a leaderboard reproduced from this checkout.

## Repository Layout

```text
ClawHazard/
├── README.md
├── docs/assets/                     # Figures extracted from the manuscript
├── eval/
│   ├── run_main.py                  # Batch evaluation entry point
│   ├── run_debug.py                 # Single-case debugging entry point
│   ├── agent/                       # FC, Codex, OpenClaw, and user-model adapters
│   ├── cases/                       # Case loading and runtime-resource resolution
│   ├── environment/                 # Mock service lifecycle and tool mapping
│   ├── evaluators/                  # Executable checks and in-run rubric judging
│   ├── specs/                       # Structured utility check specifications
│   └── tests/                       # Evaluation tests
├── tasks_filtered_unrelated_write/  # Default evaluation task root
├── tasks_filtered/                  # Fallback runtime resource pool
├── skills_v0/                       # Earlier skill packages
├── skills_v1.0/
├── skills_v2.0/
├── judge_results.py                 # Standalone rubric judging of saved traces
├── mock_service_runner.py           # Stateful service runner and audit collection
└── mock_service_utils.py            # Local service helpers
```

The figures above are extracted from Figures 1, 2, and 4 of *ClawHazard: Benchmarking the Agent Safety in Skill-Mediated Tool Use for Web Services*.
