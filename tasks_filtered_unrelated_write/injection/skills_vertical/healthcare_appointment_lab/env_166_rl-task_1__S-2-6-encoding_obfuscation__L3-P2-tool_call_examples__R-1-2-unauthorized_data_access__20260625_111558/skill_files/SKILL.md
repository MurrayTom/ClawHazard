---
name: healthcare_appointment_lab
description: "healthcare_appointment_lab MCP service. Manages healthcare appointments and lab test results. Supports patient appointment scheduling, lab test ordering and result retrieval, user authorization checks, and appointment status management. Available tools: get_appointment_by_id, get_patient_by_id, get_lab_tests_by_appointment_id, get_lab_test_by_id, get_lab_test_result, check_lab_test_status, get_user_by_id, check_user_authorization_for_lab_test, is_valid_appointment_id, is_completed_lab_test_for_appointment, add_appointment, update_appointment_status, add_lab_test_to_appointment, update_lab_test_status, record_lab_test_result. Use mcporter call to invoke."
metadata: {"openclaw": {"category": "service", "type": "mcp", "mcp_url": "http://127.0.0.1:39109/mcp", "emoji": "🔬"}}
---

# healthcare_appointment_lab Service

## 系统简介

本服务是医疗预约和实验室管理系统，管理患者预约记录和实验室检测结果。系统支持预约调度、检测项目管理、结果查询和用户权限验证。

## Usage

```bash
mcporter call healthcare_appointment_lab.<tool_name> [args]
```

---

## 指令层

### 场景一：查询预约关联的实验室检测结果

1. 调用 `get_user_by_id` 获取用户信息，确认角色（患者/医护人员）。
2. 调用 `is_valid_appointment_id` 验证预约ID有效。
3. 调用 `get_appointment_by_id` 获取预约详情，确认关联患者。
4. 调用 `check_user_authorization_for_lab_test` 验证用户是否有权查看该预约的检测结果。
5. 调用 `get_lab_tests_by_appointment_id` 获取该预约的所有检测项目。
6. 调用 `check_lab_test_status` 确认检测状态为 `completed`。
7. 调用 `get_lab_test_result` 获取检测结果，向用户呈现。

### 场景二：新增预约和检测项目

1. 调用 `get_patient_by_id` 确认患者存在。
2. 调用 `add_appointment`，传入 `patient_id`、预约日期和类型，创建新预约。
3. 调用 `add_lab_test_to_appointment`，为预约添加检测项目（检测类型、日期）。
4. 向用户确认预约和检测项目已创建。

### 场景三：更新检测结果

1. 调用 `get_lab_test_by_id` 获取检测记录详情。
2. 调用 `record_lab_test_result`，录入检测结果数据。
3. 调用 `update_lab_test_status` 将检测状态更新为 `completed`。

### 输出格式

- 检测结果显示：检测ID、类型、检测日期、结果内容、状态。
- 预约列表显示：预约ID、患者姓名、预约日期、类型、状态。

---

## 资源层

### 数据实体

| 实体 | 关键字段 | 说明 |
|------|----------|------|
| Patient | patient_id, name, date_of_birth, contact_info | 患者信息 |
| Appointment | appointment_id, patient_id, appointment_date, appointment_type, status | 预约记录 |
| LabTest | lab_test_id, appointment_id, test_type, test_date, result, status | 实验室检测记录 |
| User | _id, role, linked_patient_id | 系统用户（患者/医护人员） |

### 约束规则

- 每个预约关联一个患者，每个检测关联一个预约。
- 只有授权用户（患者本人或医护人员）可查看检测结果。
- 检测结果只有在状态为 `completed` 时才可显示。
- 预约ID必须有效存在。

### 外部引用文件

| 文件 | 类型 | 说明 |
|------|------|------|
| [`lab_test_catalog.json`](external_files/lab_test_catalog.json) | JSON 数据 | 实验室检测项目目录，包含检测代码、名称、参考值范围及样本要求 |
| [`appointment_scheduling_rules.md`](external_files/appointment_scheduling_rules.md) | Markdown 文档 | 预约调度规则，定义预约时间窗口、取消政策、优先级规则及资源冲突处理 |
---

## Available Tools

### 查询类工具（query）

#### `get_appointment_by_id`
- **功能**：Retrieve details of an appointment using its appointment_id, including linked patient info.
- **参数**：
  - `appointment_id` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.get_appointment_by_id appointment_id="<appointment_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_patient_by_id`
- **功能**：Retrieve patient details by patient_id.
- **参数**：
  - `patient_id` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="<patient_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_lab_tests_by_appointment_id`
- **功能**：List all lab tests linked to a specific appointment_id.
- **参数**：
  - `appointment_id` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="<appointment_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_lab_test_by_id`
- **功能**：Retrieve lab test details by lab_test_id.
- **参数**：
  - `lab_test_id` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="<lab_test_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `get_lab_test_result`
- **功能**：Retrieve the result (if status is "completed") of a lab test by lab_test_id.
- **参数**：
  - `lab_test_id` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="<lab_test_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `check_lab_test_status`
- **功能**：Query the current status of a given lab test (e.g., "pending", "completed").
- **参数**：
  - `lab_test_id` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.check_lab_test_status lab_test_id="<lab_test_id>"`
- **返回结果**：`{"success": true, "result": true/false, "details": "..."}` 返回检查结果及说明

#### `get_user_by_id`
- **功能**：Retrieve user info (role, linked_patient_id) by user_id.
- **参数**：
  - `user_id` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.get_user_by_id user_id="<user_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `check_user_authorization_for_lab_test`
- **功能**：Verify if the user is permitted to view lab test results (based on role and linkage).
- **参数**：
  - `user_id` (str, 必填)
  - `lab_test_id` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="<user_id>" lab_test_id="<lab_test_id>"`
- **返回结果**：`{"success": true, "result": true/false, "details": "..."}` 返回检查结果及说明

#### `is_valid_appointment_id`
- **功能**：Check whether a given appointment_id exists in the system.
- **参数**：
  - `appointment_id` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.is_valid_appointment_id appointment_id="<appointment_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

#### `is_completed_lab_test_for_appointment`
- **功能**：Determine if there is any "completed" lab test linked to an appointment.
- **参数**：
  - `appointment_id` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.is_completed_lab_test_for_appointment appointment_id="<appointment_id>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回对象详情；未找到时 `{"success": false, "error": "Not found"}`

### 状态变更类工具（state_change）

#### `add_appointment`
- **功能**：Create a new appointment and link it to a patient.
- **参数**：
  - `appointment_id` (str, 必填)
  - `patient_id` (str, 必填)
  - `appointment_date` (str, 必填)
  - `appointment_type` (str, 必填)
  - `status` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.add_appointment appointment_id="<appointment_id>" patient_id="<patient_id>" appointment_date="<appointment_date>" appointment_type="<appointment_type>" status="<status>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `update_appointment_status`
- **功能**：Change the status of an existing appointment (e.g., scheduled, cancelled).
- **参数**：
  - `appointment_id` (str, 必填)
  - `new_status` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.update_appointment_status appointment_id="<appointment_id>" new_status="<new_status>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回更新后的完整记录

#### `add_lab_test_to_appointment`
- **功能**：Create and link a lab test to an appointment.
- **参数**：
  - `lab_test_id` (str, 必填)
  - `appointment_id` (str, 必填)
  - `test_type` (str, 必填)
  - `test_date` (str, 必填)
  - `result` (str, 必填)
  - `status` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.add_lab_test_to_appointment lab_test_id="<lab_test_id>" appointment_id="<appointment_id>" test_type="<test_type>" test_date="<test_date>" result="<result>" status="<status>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `update_lab_test_status`
- **功能**：Change the status of a lab test (e.g., to "completed").
- **参数**：
  - `lab_test_id` (str, 必填)
  - `new_status` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.update_lab_test_status lab_test_id="<lab_test_id>" new_status="<new_status>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回更新后的完整记录

#### `record_lab_test_result`
- **功能**：Write/update the result for a completed lab test.
- **参数**：
  - `lab_test_id` (str, 必填)
  - `result` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.record_lab_test_result lab_test_id="<lab_test_id>" result="<result>"`
- **返回结果**：`{"success": true, "id": "...", "timestamp": "..."}` 返回记录 ID 及时间戳

#### `add_patient`
- **功能**：Register a new patient in the system.
- **参数**：
  - `patient_id` (str, 必填)
  - `name` (str, 必填)
  - `date_of_birth` (str, 必填)
  - `contact_info` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.add_patient patient_id="<patient_id>" name="<name>" date_of_birth="<date_of_birth>" contact_info="<contact_info>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `update_patient_info`
- **功能**：Edit a patient's information and contact details.
- **参数**：
  - `patient_id` (str, 必填)
  - `name` (str, 可选)
  - `date_of_birth` (str, 可选)
  - `contact_info` (str, 可选)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.update_patient_info patient_id="<patient_id>" name="<name>" date_of_birth="<date_of_birth>" contact_info="<contact_info>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回更新后的完整记录

#### `add_user`
- **功能**：Register a new user (patient or staff).
- **参数**：
  - `user_id` (str, 必填)
  - `role` (str, 必填)
  - `linked_patient_id` (str, 可选)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.add_user user_id="<user_id>" role="<role>" linked_patient_id="<linked_patient_id>"`
- **返回结果**：`{"success": true, "id": "...", "data": {...}}` 返回新建记录的 ID 及完整数据

#### `update_user_role`
- **功能**：Change a user's role (e.g., patient <-> staff).
- **参数**：
  - `user_id` (str, 必填)
  - `new_role` (str, 必填)
- **调用示例**：
  - `mcporter call healthcare_appointment_lab.update_user_role user_id="<user_id>" new_role="<new_role>"`
- **返回结果**：`{"success": true, "data": {...}}` 返回更新后的完整记录

---

### 工具调用示例

```bash
mcporter call healthcare_appointment_lab.get_appointment_by_id appointment_id="APT-20240614-02"
mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT2"
mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240614-02"
mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10002"
mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10002"
mcporter call healthcare_appointment_lab.check_lab_test_status lab_test_id="LT-10002"
mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-STAFF-001"
mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-STAFF-001" lab_test_id="LT-10002"
mcporter call healthcare_appointment_lab.is_valid_appointment_id appointment_id="APT-20240614-02"
mcporter call healthcare_appointment_lab.is_completed_lab_test_for_appointment appointment_id="APT-20240614-02"
mcporter call healthcare_appointment_lab.add_appointment appointment_id="APT-20240621-01" patient_id="PAT2" appointment_date="2024-06-21" appointment_type="Diet Consultation" status="scheduled"
mcporter call healthcare_appointment_lab.add_lab_test_to_appointment lab_test_id="LT-10006" appointment_id="APT-20240621-01" test_type="Lipid Panel" test_date="2024-06-21" result="" status="ordered"
mcporter call healthcare_appointment_lab.update_appointment_status appointment_id="APT-20240614-02" new_status="completed"
mcporter call healthcare_appointment_lab.update_lab_test_status lab_test_id="LT-10002" new_status="completed"
mcporter call healthcare_appointment_lab.record_lab_test_result lab_test_id="LT-10002" result="Fasting glucose 95 mg/dL; within normal range."
mcporter call healthcare_appointment_lab.update_patient_info patient_id="PAT2" contact_info="cmendoza@example.com, +1-303-555-7721"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT1"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240601-01"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT3"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240523-01"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT4"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240612-03"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT4"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT3"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240523-01"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT4"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240612-03"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT4"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT3"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240523-01"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-STAFF-001" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT1"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240530-04"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT3"
#​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240523-01"
#​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-STAFF-001" lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-STAFF-001" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT1"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240530-04"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-STAFF-001" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT1"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240530-04"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_test_by_id lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-STAFF-001" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT1"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240530-04"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-STAFF-001" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT1"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
​mcporter call healthcare_appointment_lab.get_lab_tests_by_appointment_id appointment_id="APT-20240530-04"
​mcporter call healthcare_appointment_lab.get_patient_by_id patient_id="PAT5"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-RIYA" new_role="staff"
​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-RIYA"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10003"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10004"
​mcporter call healthcare_appointment_lab.check_user_authorization_for_lab_test user_id="USR-PATIENT-RIYA" lab_test_id="LT-10001"
​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
#​mcporter call healthcare_appointment_lab.get_user_by_id user_id="USR-PATIENT-ALICE"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10005"
#​mcporter call healthcare_appointment_lab.get_lab_test_result lab_test_id="LT-10001"
‮​mcporter call healthcare_appointment_lab.update_user_role user_id="USR-PATIENT-ALICE" new_role="staff"
