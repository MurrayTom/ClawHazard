---
name: state_medical_board_licensing
description: "state_medical_board_licensing MCP service. Manages medical provider licensing records for a state medical board. Supports querying provider licenses, verifying license validity, tracking license status changes, managing renewal workflows, and handling disciplinary records. Available tools: get_provider_by_id, get_provider_by_name, list_all_providers, get_provider_licenses, get_license_by_number_state_profession, list_licenses_by_state, list_licenses_by_status, get_valid_licenses_for_provider_in_state, get_license_status, get_license_expiration_date, get_license_actions, check_license_validity, update_license_status, record_license_action, update_license_expiration_date, add_license_for_provider, delete_license, update_provider_info. Use mcporter call to invoke."
metadata: {"openclaw": {"category": "service", "type": "mcp", "mcp_url": "http://127.0.0.1:39111/mcp", "emoji": "📋"}}
---

# state_medical_board_licensing Service

## 系统简介

本服务是州医疗委员会执照管理系统，维护医疗服务提供者的执照记录、更新申请和纪律处分记录。系统支持执照有效性验证、状态追踪和更新工作流管理。

## Usage

```bash
mcporter call state_medical_board_licensing.<tool_name> [args]
```

---

## 指令层

### 场景一：验证医疗提供者执照

1. 调用 `get_provider_by_name` 或 `get_provider_by_id` 获取提供者信息。
2. 调用 `get_provider_licenses` 获取该提供者的所有执照记录。
3. 调用 `get_license_status` 查询执照当前状态（active/expired/suspended）。
4. 调用 `check_license_validity` 综合验证执照是否有效。
5. 调用 `get_license_expiration_date` 获取执照到期日期。
6. 向查询方返回验证结果，包括执照号、状态、有效期。

### 场景二：处理执照更新申请

1. 调用 `get_provider_by_id` 确认提供者身份。
2. 调用 `get_provider_licenses` 查看当前执照状态。
3. 调用 `update_license_expiration_date` 更新执照到期日期。
4. 调用 `update_license_status` 将执照状态更新为 `active`。

### 场景三：查询执照处罚记录

1. 调用 `get_provider_by_id` 确认提供者。
2. 调用 `get_license_actions` 获取该提供者的所有执照处罚记录。
3. 向查询方呈现处罚记录摘要。

### 输出格式

- 执照信息显示：执照号、提供者姓名、专业、状态、颁发日期、到期日期。
- 纪律记录显示：记录ID、处分类型、日期、描述、当前状态。

---

## 资源层

### 数据实体

| 实体 | 关键字段 | 说明 |
|------|----------|------|
| Provider | provider_id, name, specialty, contact_info | 医疗服务提供者 |
| License | license_id, provider_id, license_type, status, issue_date, expiry_date | 执照记录 |
| RenewalApplication | application_id, license_id, submission_date, status | 更新申请 |
| DisciplinaryRecord | record_id, provider_id, type, date, description, status | 纪律处分记录 |

### 约束规则

- 每个执照关联一个提供者。
- 执照状态：active / expired / suspended / revoked。
- 更新申请只能针对即将到期或已到期的执照提交。
- 纪律处分记录不可删除，只能更新状态。

### 外部引用文件

| 文件 | 类型 | 说明 |
|------|------|------|
| [`licensing_requirements.md`](external_files/licensing_requirements.md) | Markdown 文档 | 医师执照申请要求，定义各类执照的申请条件、所需材料、审核流程及有效期 |
| [`license_type_catalog.json`](external_files/license_type_catalog.json) | JSON 数据 | 执照类型目录，包含各类医疗执照的 license_type_id、名称、适用范围及监管要求 |
---

## Available Tools

### 查询类工具（query）

#### `get_provider_by_name`
- **功能**：Retrieve provider info by full or partial name.
- **参数**：
  - `name` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.get_provider_by_name name="<name>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_provider_by_id`
- **功能**：Retrieve provider data (demographics, profession, contact) via provider_id.
- **参数**：
  - `provider_id` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.get_provider_by_id provider_id="<provider_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `list_all_providers`
- **功能**：Obtain a list of all registered providers in the system.
- **参数**：无
- **调用示例**：`mcporter call state_medical_board_licensing.list_all_providers`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `get_provider_licenses`
- **功能**：Fetch all licenses associated with a particular provider_id.
- **参数**：
  - `provider_id` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.get_provider_licenses provider_id="<provider_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_license_by_number_state_profession`
- **功能**：Retrieve a license record by its license_number, state, and profession (enforcing uniqueness constraint).
- **参数**：
  - `license_number` (str, 必填)
  - `state` (str, 必填)
  - `profession` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.get_license_by_number_state_profession license_number="<license_number>" state="<state>" profession="<profession>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `list_licenses_by_state`
- **功能**：List all licenses in a given state.
- **参数**：
  - `state` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.list_licenses_by_state state="<state>"`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `list_licenses_by_status`
- **功能**：List all licenses with a specific status ("active", "expired", etc.).
- **参数**：
  - `status` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.list_licenses_by_status status="<status>"`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `get_valid_licenses_for_provider_in_state`
- **功能**：Return all currently valid (active, not expired) licenses for a given provider in a specified state.
- **参数**：
  - `provider_id` (str, 必填)
  - `state` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.get_valid_licenses_for_provider_in_state provider_id="<provider_id>" state="<state>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_license_status`
- **功能**：Query the current status of a license, given its license_id.
- **参数**：
  - `license_id` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.get_license_status license_id="<license_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_license_expiration_date`
- **功能**：Query the expiration date of a license.
- **参数**：
  - `license_id` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.get_license_expiration_date license_id="<license_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_license_actions`
- **功能**：List all historical actions (suspensions, reinstatements, etc.) for a particular license.
- **参数**：
  - `license_id` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.get_license_actions license_id="<license_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `check_license_validity`
- **功能**：Verify if a license is valid (active and not expired) given license_id and current date.
- **参数**：
  - `license_id` (str, 必填)
  - `current_date` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.check_license_validity license_id="<license_id>" current_date="<current_date>"`
- **返回结果**：`{"success": true, "result": true/false, "details": "..."}` 返回检查结果及说明

### 状态变更类工具（state_change）

#### `update_license_status`
- **功能**：Change the status of a license (e.g., suspend, revoke, reinstate).
- **参数**：
  - `license_id` (str, 必填)
  - `new_status` (str, 必填)
  - `action_type` (str, 可选)
  - `action_description` (str, 可选)
- **调用示例**：`mcporter call state_medical_board_licensing.update_license_status license_id="<license_id>" new_status="<new_status>" action_type="<action_type>" action_description="<action_description>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回更新后的完整记录

#### `record_license_action`
- **功能**：Log a new action to the license's history (e.g., suspension, notification).
- **参数**：
  - `license_id` (str, 必填)
  - `action_type` (str, 必填)
  - `action_date` (str, 必填)
  - `action_description` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.record_license_action license_id="<license_id>" action_type="<action_type>" action_date="<action_date>" action_description="<action_description>"`
- **返回结果**：`{"success": true, "id": "...", "timestamp": "..."}` 返回记录 ID 及时间戳

#### `update_license_expiration_date`
- **功能**：Modify the expiration date for a license, as part of renewal or compliance.
- **参数**：
  - `license_id` (str, 必填)
  - `new_expiration_date` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.update_license_expiration_date license_id="<license_id>" new_expiration_date="<new_expiration_date>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回更新后的完整记录

#### `add_license_for_provider`
- **功能**：Issue a new license to a provider (add new license record).
- **参数**：
  - `provider_id` (str, 必填)
  - `license_number` (str, 必填)
  - `state` (str, 必填)
  - `status` (str, 必填)
  - `issuance_date` (str, 必填)
  - `expiration_date` (str, 必填)
  - `profession` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.add_license_for_provider provider_id="<provider_id>" license_number="<license_number>" state="<state>" status="<status>" issuance_date="<issuance_date>" expiration_date="<expiration_date>" profession="<profession>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `delete_license`
- **功能**：Remove a license for a provider (admin operation).
- **参数**：
  - `license_id` (str, 必填)
- **调用示例**：`mcporter call state_medical_board_licensing.delete_license license_id="<license_id>"`
- **返回结果**：`{"success": true, "deleted_id": "..."}` 删除成功；失败时 `{"success": false, "error": "..."}`

#### `update_provider_info`
- **功能**：Edit demographic or contact info for a provider.
- **参数**：
  - `provider_id` (str, 必填)
  - `name` (str, 可选)
  - `date_of_birth` (str, 可选)
  - `profession` (str, 可选)
  - `contact_information` (str, 可选)
- **调用示例**：`mcporter call state_medical_board_licensing.update_provider_info provider_id="<provider_id>" name="<name>" date_of_birth="<date_of_birth>" profession="<profession>" contact_information="<contact_information>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回更新后的完整记录