---
name: employee_benefits_enrollment
description: "employee_benefits_enrollment MCP service. Manages employee benefits enrollment including health insurance, retirement plans, and other benefit programs. Supports querying available benefits, enrollment management, dependent management, and enrollment period tracking. Available tools: get_employee_by_id, list_active_enrollment_periods, get_current_active_enrollment_period, get_employee_eligibility_profile, list_all_benefit_plans, list_benefit_plans_by_type, list_eligible_benefit_plans_for_employee, list_available_plan_options_for_employee_in_open_enrollment, get_plan_details, get_employee_plan_selections_in_period, get_employee_current_selection, enroll_employee_in_plan, change_employee_plan_selection, withdraw_employee_plan_selection, create_new_enrollment_period, activate_enrollment_period, deactivate_enrollment_period, add_benefit_plan, update_benefit_plan, remove_plan_from_employee_selection. Use mcporter call to invoke."
metadata: {"openclaw": {"category": "service", "type": "mcp", "mcp_url": "http://127.0.0.1:39115/mcp", "emoji": "👔"}}
---

# employee_benefits_enrollment Service

## 系统简介

本服务是员工福利注册门户，管理员工的健康保险、退休计划等福利项目的注册和管理。支持福利查询、注册管理、受抚养人管理和注册期追踪。

## Usage

```bash
mcporter call employee_benefits_enrollment.<tool_name> [args]
```

---

## 指令层

### 场景一：员工福利注册

1. 调用 `get_employee_by_id` 确认员工身份。
2. 调用 `get_employee_eligibility_profile` 验证员工是否符合注册条件。
3. 调用 `get_current_active_enrollment_period` 确认当前处于注册期内。
4. 调用 `list_eligible_benefit_plans_for_employee` 获取员工可用的福利项目列表。
5. 调用 `get_plan_details` 查询目标福利的详细信息。
6. 调用 `enroll_employee_in_plan`，传入 `employee_id` 和 `plan_id`，完成注册。

### 场景二：更改福利选择

1. 调用 `get_employee_current_selection` 查看员工当前的福利选择。
2. 调用 `list_available_plan_options_for_employee_in_open_enrollment` 获取当前开放注册期的可选方案。
3. 调用 `change_employee_plan_selection` 更新员工的福利选择。

### 场景三：查询注册状态

1. 调用 `get_employee_plan_selections_in_period` 获取员工在指定注册期内的所有福利选择记录。
2. 调用 `get_employee_current_selection` 查看当前生效的注册详细信息。
### 输出格式

- 福利列表显示：福利ID、名称、类型、覆盖范围、月费用。
- 注册记录显示：注册ID、福利名称、生效日期、状态、受抚养人。

---

## 资源层

### 数据实体

| 实体 | 关键字段 | 说明 |
|------|----------|------|
| Employee | employee_id, name, department, hire_date, status | 员工档案 |
| Benefit | benefit_id, name, type, coverage, cost | 福利项目 |
| Enrollment | enrollment_id, employee_id, benefit_id, effective_date, status | 注册记录 |
| Dependent | dependent_id, employee_id, name, relationship, date_of_birth | 受抚养人信息 |

### 约束规则

- 员工必须在注册期内完成注册。
- 员工必须符合资格条件才能注册特定福利。
- 每个员工同一福利项目只能有一条有效注册记录。

### 外部引用文件

| 文件 | 类型 | 说明 |
|------|------|------|
| [`benefits_catalog.json`](external_files/benefits_catalog.json) | JSON 数据 | 员工福利项目目录，包含各福利计划的 plan_id、名称、覆盖范围、费率及资格条件 |
| [`enrollment_rules.md`](external_files/enrollment_rules.md) | Markdown 文档 | 福利注册规则文档，说明开放注册期、资格变更事件、等待期及依赖关系规则 |
---

## Available Tools

### 查询类工具（query）

#### `get_employee_by_id`
- **功能**：Retrieve info for a specific employee by ID.
- **参数**：
  - `employee_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.get_employee_by_id employee_id="<employee_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `list_active_enrollment_periods`
- **功能**：Get all currently open enrollment periods (with is_active = True).
- **参数**：无
- **调用示例**：`mcporter call employee_benefits_enrollment.list_active_enrollment_periods`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `get_current_active_enrollment_period`
- **功能**：Return the (single) currently open enrollment period if one exists.
- **参数**：无
- **调用示例**：`mcporter call employee_benefits_enrollment.get_current_active_enrollment_period`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_employee_eligibility_profile`
- **功能**：Query the eligibility profile string of an employee.
- **参数**：
  - `employee_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.get_employee_eligibility_profile employee_id="<employee_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `list_all_benefit_plans`
- **功能**：Get all available benefit plans in the system (unfiltered).
- **参数**：无
- **调用示例**：`mcporter call employee_benefits_enrollment.list_all_benefit_plans`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `list_benefit_plans_by_type`
- **功能**：Get benefit plans filtered by plan_type (e.g., "health insurance").
- **参数**：
  - `plan_type` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.list_benefit_plans_by_type plan_type="<plan_type>"`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `list_eligible_benefit_plans_for_employee`
- **功能**：List benefit plans that match the employee's eligibility profile and are available to them.
- **参数**：
  - `employee_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.list_eligible_benefit_plans_for_employee employee_id="<employee_id>"`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `list_available_plan_options_for_employee_in_open_enrollment`
- **功能**：List benefit plans that are both eligible for the employee and selectable in the current active enrollment period.
- **参数**：
  - `employee_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.list_available_plan_options_for_employee_in_open_enrollment employee_id="<employee_id>"`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `get_plan_details`
- **功能**：Retrieve full details for a benefit plan by plan_id.
- **参数**：
  - `plan_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.get_plan_details plan_id="<plan_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_employee_plan_selections_in_period`
- **功能**：List employee’s plan selections for a given enrollment period.
- **参数**：
  - `employee_id` (str, 必填)
  - `enrollment_period_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.get_employee_plan_selections_in_period employee_id="<employee_id>" enrollment_period_id="<enrollment_period_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_employee_current_selection`
- **功能**：Get the currently active plan selection for an employee (if any) during the active enrollment period.
- **参数**：
  - `employee_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.get_employee_current_selection employee_id="<employee_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

### 状态变更类工具（state_change）

#### `enroll_employee_in_plan`
- **功能**：Add or update an employee’s plan selection during an active enrollment period (must pass eligibility and active period checks).
- **参数**：
  - `employee_id` (str, 必填)
  - `plan_id` (str, 必填)
  - `enrollment_period_id` (str, 必填)
  - `selection_date` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.enroll_employee_in_plan employee_id="<employee_id>" plan_id="<plan_id>" enrollment_period_id="<enrollment_period_id>" selection_date="<selection_date>"`
- **返回结果**：`{"success": true, "data": {...}}` 操作成功；失败时 `{"success": false, "error": "..."}`

#### `change_employee_plan_selection`
- **功能**：Modify/replace the selected plan for an employee within the current enrollment period.
- **参数**：
  - `employee_id` (str, 必填)
  - `new_plan_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.change_employee_plan_selection employee_id="<employee_id>" new_plan_id="<new_plan_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 操作成功；失败时 `{"success": false, "error": "..."}`

#### `withdraw_employee_plan_selection`
- **功能**：Remove an employee’s plan selection (e.g., if they wish to opt out) for the current enrollment period.
- **参数**：
  - `employee_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.withdraw_employee_plan_selection employee_id="<employee_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 操作成功；失败时 `{"success": false, "error": "..."}`

#### `create_new_enrollment_period`
- **功能**：Add a new enrollment period to the portal (admin action).
- **参数**：
  - `enrollment_period_id` (str, 必填)
  - `start_date` (str, 必填)
  - `end_date` (str, 必填)
  - `is_active` (bool, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.create_new_enrollment_period enrollment_period_id="<enrollment_period_id>" start_date="<start_date>" end_date="<end_date>" is_active=true`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `activate_enrollment_period`
- **功能**：Set an enrollment period’s status to active.
- **参数**：
  - `enrollment_period_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.activate_enrollment_period enrollment_period_id="<enrollment_period_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 操作成功；失败时 `{"success": false, "error": "..."}`

#### `deactivate_enrollment_period`
- **功能**：Set an enrollment period’s status to inactive.
- **参数**：
  - `enrollment_period_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.deactivate_enrollment_period enrollment_period_id="<enrollment_period_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 操作成功；失败时 `{"success": false, "error": "..."}`

#### `add_benefit_plan`
- **功能**：Add a new benefit plan to the catalog.
- **参数**：
  - `plan_id` (str, 必填)
  - `plan_type` (str, 必填)
  - `name` (str, 必填)
  - `coverage_details` (str, 必填)
  - `premiums` (float, 必填)
  - `eligibility_criteria` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.add_benefit_plan plan_id="<plan_id>" plan_type="<plan_type>" name="<name>" coverage_details="<coverage_details>" premiums="<premiums>" eligibility_criteria="<eligibility_criteria>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `update_benefit_plan`
- **功能**：Modify the attributes/details of a benefit plan (admin action).
- **参数**：
  - `plan_id` (str, 必填)
  - `plan_type` (str, 可选)
  - `name` (str, 可选)
  - `coverage_details` (str, 可选)
  - `premiums` (float, 可选)
  - `eligibility_criteria` (str, 可选)
- **调用示例**：`mcporter call employee_benefits_enrollment.update_benefit_plan plan_id="<plan_id>" plan_type="<plan_type>" name="<name>" coverage_details="<coverage_details>" premiums="<premiums>" eligibility_criteria="<eligibility_criteria>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回更新后的完整记录

#### `remove_plan_from_employee_selection`
- **功能**：Remove a specific plan selection record for an employee (admin, or self-service if allowed).
- **参数**：
  - `employee_id` (str, 必填)
  - `enrollment_period_id` (str, 必填)
  - `plan_id` (str, 必填)
- **调用示例**：`mcporter call employee_benefits_enrollment.remove_plan_from_employee_selection employee_id="<employee_id>" enrollment_period_id="<enrollment_period_id>" plan_id="<plan_id>"`
- **返回结果**：`{"success": true, "deleted_id": "..."}` 删除成功；失败时 `{"success": false, "error": "..."}`