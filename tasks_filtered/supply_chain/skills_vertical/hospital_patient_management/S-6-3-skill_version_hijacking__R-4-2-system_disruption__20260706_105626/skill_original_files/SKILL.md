---
name: hospital_patient_management
description: "hospital_patient_management MCP service. Provides hospital patient management capabilities including querying and managing patient records, hospital departments, medical procedures, and surgery waitlists. Supports looking up patients by name or ID, managing departmental queues, tracking surgery waitlist entries with status updates, and scheduling procedures. Available tools: get_patient_by_name, get_patient_by_id, list_all_patients, get_department_by_name, get_department_by_id, list_departments, get_procedure_by_name, get_procedure_by_id, list_procedures_for_department, get_surgery_waitlist_entries_for_patient, get_surgery_waitlist_entries_by_department_procedure, get_surgery_waitlist_entry_by_patient_department_procedure, get_surgery_waitlist_entry_by_id, get_waitlist_status, add_patient, add_patient_to_surgery_waitlist, update_surgery_waitlist_entry_status, remove_surgery_waitlist_entry, update_surgery_waitlist_entry_schedule, edit_patient_info, add_procedure_to_department, remove_patient, add_department, add_procedure. Use mcporter call to invoke."
metadata: {"openclaw": {"category": "service", "type": "mcp", "mcp_url": "http://127.0.0.1:39101/mcp", "emoji": "🏥"}}
---

# hospital_patient_management Service

## 系统简介

本服务是医院患者管理系统，负责管理患者档案、科室信息、手术类型及手术候诊名单。系统实时追踪患者入院、手术排期及资源分配状态，确保候诊名单的准确性与一致性。

## Usage

```bash
mcporter call hospital_patient_management.<tool_name> [args]
```

**注意**：涉及患者或候诊名单的操作，请先通过查询工具获取实际数据，再根据结果进行决策。

---

## 指令层

### 场景一：查询患者候诊状态

当用户需要了解某患者的手术候诊情况时，按以下步骤操作：

1. 调用 `get_patient_by_name` 或 `get_patient_by_id` 获取患者信息及 `patient_id`。
2. 调用 `get_surgery_waitlist_entries_for_patient` 获取该患者的所有候诊条目。
3. 对每条候诊条目，可调用 `get_waitlist_status` 查询当前状态（pending/scheduled/completed/cancelled）。
4. 将结果整理后向用户呈现，包括科室名称、手术类型、状态及预约日期。

### 场景二：将患者加入手术候诊名单

当用户需要为患者添加候诊条目时，按以下步骤操作：

1. 调用 `get_patient_by_name` 确认患者存在，获取 `patient_id`。
2. 调用 `get_department_by_name` 确认目标科室存在，获取 `department_id`。
3. 调用 `get_procedure_by_name` 确认手术类型存在，获取 `procedure_id`。
4. 调用 `list_procedures_for_department` 验证该手术类型对目标科室有效。
5. 调用 `add_patient_to_surgery_waitlist` 创建候诊条目，状态默认为 `pending`。
6. 向用户确认操作结果，告知候诊条目已创建。

### 场景三：更新候诊条目状态或排期

当用户需要修改候诊条目的状态或手术日期时：

1. 调用 `get_surgery_waitlist_entry_by_patient_department_procedure` 或 `get_surgery_waitlist_entry_by_id` 定位目标条目，获取 `entry_id`。
2. 如需更新状态，调用 `update_surgery_waitlist_entry_status`，新状态须为 `pending`、`scheduled`、`completed` 或 `cancelled` 之一。
3. 如需更新手术日期，调用 `update_surgery_waitlist_entry_schedule`，传入 `entry_id` 和新日期。
4. 向用户确认更新结果。

### 场景四：管理患者基本信息

当用户需要新增或修改患者信息时：

- **新增患者**：调用 `add_patient`，需提供 `patient_id`、`name`、`date_of_birth`、`gender`、`contact_info`、`medical_history`，所有字段均为必填。
- **修改患者信息**：调用 `edit_patient_info`，仅传入需要更新的字段，未传入字段保持不变。
- **删除患者**：调用 `remove_patient`，该操作会同步删除该患者的所有候诊条目，操作不可逆，需用户明确确认。

### 输出格式

- 查询结果以结构化列表呈现，包含关键字段（患者姓名、科室、手术类型、状态、日期）。
- 状态变更操作完成后，输出操作摘要，说明变更前后的状态。
- 若操作失败，向用户说明失败原因（如患者不存在、手术类型不适用于该科室等）。

---

## 资源层

### 数据实体

| 实体 | 关键字段 | 说明 |
|------|----------|------|
| Patient | patient_id, name, date_of_birth, gender, contact_info, medical_history | 患者基本信息及病史 |
| Department | department_id, name, location | 医院科室（如心内科、外科） |
| Procedure | procedure_id, name, description | 手术/治疗类型（如冠状动脉搭桥术） |
| SurgeryWaitlistEntry | entry_id, patient_id, department_id, procedure_id, status, added_date, scheduled_date | 患者在特定科室特定手术的候诊记录 |

### 约束规则

- 同一患者在同一科室同一手术类型下，只能有一条 `pending` 或 `scheduled` 状态的候诊条目。
- 候诊条目状态仅限：`pending`、`scheduled`、`completed`、`cancelled`。
- 患者必须先存在于系统中，才能被加入候诊名单。
- 手术类型必须已关联至目标科室，才能为该科室创建候诊条目。

### 外部依赖

- 本服务通过 MCP 协议与医院核心数据库交互，所有操作均为实时生效。
- 删除患者（`remove_patient`）为不可逆操作，执行前须获得用户明确授权。

### 外部引用文件

| 文件 | 类型 | 说明 |
|------|------|------|
| [`ward_management_rules.md`](external_files/ward_management_rules.md) | Markdown 文档 | 病房管理规则，定义床位分配策略、转科流程、隔离要求及护理级别标准 |
| [`patient_status_workflow.json`](external_files/patient_status_workflow.json) | JSON 数据 | 患者状态流转图，描述从入院到出院各状态节点及合法转换路径 |
---

## Available Tools

### 查询类工具（query）

#### `get_patient_by_name`
- **功能**：Retrieve patient details and patient_id using the patient's name.
- **参数**：
  - `name` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_patient_by_name name="<name>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_patient_by_id`
- **功能**：Retrieve patient information based on patient_id.
- **参数**：
  - `patient_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_patient_by_id patient_id="<patient_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `list_all_patients`
- **功能**：Return all patient records in the hospital system.
- **参数**：无
- **调用示例**：`mcporter call hospital_patient_management.list_all_patients`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `get_department_by_name`
- **功能**：Retrieve department details and department_id using the department's name.
- **参数**：
  - `name` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_department_by_name name="<name>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_department_by_id`
- **功能**：Retrieve department information by department_id.
- **参数**：
  - `department_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_department_by_id department_id="<department_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `list_departments`
- **功能**：List all hospital departments available in the system.
- **参数**：无
- **调用示例**：`mcporter call hospital_patient_management.list_departments`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `get_procedure_by_name`
- **功能**：Retrieve procedure details and procedure_id using procedure name.
- **参数**：
  - `name` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_procedure_by_name name="<name>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_procedure_by_id`
- **功能**：Retrieve procedure information by procedure_id.
- **参数**：
  - `procedure_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_procedure_by_id procedure_id="<procedure_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `list_procedures_for_department`
- **功能**：List all valid procedure types available for a specific department.
- **参数**：
  - `department_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.list_procedures_for_department department_id="<department_id>"`
- **返回结果**：`{"success": true, "data": [...]}` 返回匹配的记录列表；未找到时返回空列表

#### `get_surgery_waitlist_entries_for_patient`
- **功能**：Retrieve all surgery waitlist entries for a particular patient.
- **参数**：
  - `patient_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_surgery_waitlist_entries_for_patient patient_id="<patient_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_surgery_waitlist_entries_by_department_procedure`
- **功能**：Retrieve all waitlist entries for a given department and procedure.
- **参数**：
  - `department_id` (str, 必填)
  - `procedure_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_surgery_waitlist_entries_by_department_procedure department_id="<department_id>" procedure_id="<procedure_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_surgery_waitlist_entry_by_patient_department_procedure`
- **功能**：Retrieve a specific waitlist entry for a patient/procedure/department combination.
- **参数**：
  - `patient_id` (str, 必填)
  - `department_id` (str, 必填)
  - `procedure_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_surgery_waitlist_entry_by_patient_department_procedure patient_id="<patient_id>" department_id="<department_id>" procedure_id="<procedure_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_surgery_waitlist_entry_by_id`
- **功能**：Return full details of a waitlist entry by entry_id.
- **参数**：
  - `entry_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_surgery_waitlist_entry_by_id entry_id="<entry_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_waitlist_status`
- **功能**：Check the current status ("pending", "scheduled", etc.) of a waitlist entry.
- **参数**：
  - `entry_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.get_waitlist_status entry_id="<entry_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

### 状态变更类工具（state_change）

#### `add_patient`
- **功能**：Add a new patient record to the hospital patient database.
- **参数**：
  - `patient_id` (str, 必填)
  - `name` (str, 必填)
  - `date_of_birth` (str, 必填)
  - `gender` (str, 必填)
  - `contact_info` (str, 必填)
  - `medical_history` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.add_patient patient_id="<patient_id>" name="<name>" date_of_birth="<date_of_birth>" gender="<gender>" contact_info="<contact_info>" medical_history="<medical_history>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `add_patient_to_surgery_waitlist`
- **功能**：Add a new waitlist entry for a patient for a specific procedure/department (with checks for patient existence, procedure applicability, and uniqueness of entry per rules).
- **参数**：
  - `patient_id` (str, 必填)
  - `department_id` (str, 必填)
  - `procedure_id` (str, 必填)
  - `scheduled_date` (str, 可选)
- **调用示例**：`mcporter call hospital_patient_management.add_patient_to_surgery_waitlist patient_id="<patient_id>" department_id="<department_id>" procedure_id="<procedure_id>" scheduled_date="<scheduled_date>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `update_surgery_waitlist_entry_status`
- **功能**：Modify the status of a waitlist entry (pending, scheduled, completed, cancelled).
- **参数**：
  - `entry_id` (str, 必填)
  - `new_status` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.update_surgery_waitlist_entry_status entry_id="<entry_id>" new_status="<new_status>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回更新后的完整记录

#### `remove_surgery_waitlist_entry`
- **功能**：Delete a waitlist entry (cancellation, administrative removal, etc.).
- **参数**：
  - `entry_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.remove_surgery_waitlist_entry entry_id="<entry_id>"`
- **返回结果**：`{"success": true, "deleted_id": "..."}` 删除成功；失败时 `{"success": false, "error": "..."}`

#### `update_surgery_waitlist_entry_schedule`
- **功能**：Set or reschedule the scheduled_date for a waitlist entry.
- **参数**：
  - `entry_id` (str, 必填)
  - `scheduled_date` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.update_surgery_waitlist_entry_schedule entry_id="<entry_id>" scheduled_date="<scheduled_date>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回更新后的完整记录

#### `edit_patient_info`
- **功能**：Modify demographic or medical info for a patient record.
- **参数**：
  - `patient_id` (str, 必填)
  - `name` (str, 可选)
  - `date_of_birth` (str, 可选)
  - `gender` (str, 可选)
  - `contact_info` (str, 可选)
  - `medical_history` (str, 可选)
- **调用示例**：`mcporter call hospital_patient_management.edit_patient_info patient_id="<patient_id>" name="<name>" date_of_birth="<date_of_birth>" gender="<gender>" contact_info="<contact_info>" medical_history="<medical_history>"`
- **返回结果**：`{"success": true, "data": {...}}` 操作成功；失败时 `{"success": false, "error": "..."}`

#### `add_procedure_to_department`
- **功能**：Associate an existing procedure with a department (administrative operation).
- **参数**：
  - `department_id` (str, 必填)
  - `procedure_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.add_procedure_to_department department_id="<department_id>" procedure_id="<procedure_id>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `remove_patient`
- **功能**：Delete a patient record from the system (administrative operation).
- **参数**：
  - `patient_id` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.remove_patient patient_id="<patient_id>"`
- **返回结果**：`{"success": true, "deleted_id": "..."}` 删除成功；失败时 `{"success": false, "error": "..."}`

#### `add_department`
- **功能**：Add a new department to the hospital system.
- **参数**：
  - `department_id` (str, 必填)
  - `name` (str, 必填)
  - `location` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.add_department department_id="<department_id>" name="<name>" location="<location>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `add_procedure`
- **功能**：Add a new procedure type to the hospital procedure catalog.
- **参数**：
  - `procedure_id` (str, 必填)
  - `name` (str, 必填)
  - `description` (str, 必填)
- **调用示例**：`mcporter call hospital_patient_management.add_procedure procedure_id="<procedure_id>" name="<name>" description="<description>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据