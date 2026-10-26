"""Task Todo Manager mock server."""

import json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from env_class import TaskTodoManagerSystem

app = FastAPI(title="Task Todo Manager Mock Server")

_seed_path = Path(__file__).parent / "task_todo_manager_task_1.json"
_seed = json.loads(_seed_path.read_text(encoding="utf-8"))
_env = TaskTodoManagerSystem(init_config=_seed["init_config"])
_env.user_profile = _seed["init_config"]["user_profile"]
_env.projects = _seed["init_config"]["projects"]
_env.tasks = _seed["init_config"]["tasks"]
_env.subtasks = _seed["init_config"]["subtasks"]
_env.comments = _seed["init_config"]["comments"]
_env.labels = _seed["init_config"]["labels"]


@app.get("/get_user_profile")
def get_user_profile():
    return _env.get_user_profile()


@app.get("/list_projects")
def list_projects():
    return _env.list_projects()


@app.get("/get_project_by_id")
def get_project_by_id(project_id: str):
    return _env.get_project_by_id(project_id=project_id)


@app.get("/list_tasks_in_project")
def list_tasks_in_project(project_id: str, status: str = "", sort_by: str = "created_at"):
    return _env.list_tasks_in_project(project_id=project_id, status=status or None, sort_by=sort_by)


@app.get("/get_task_by_id")
def get_task_by_id(task_id: str):
    return _env.get_task_by_id(task_id=task_id)


@app.get("/search_tasks")
def search_tasks(query: str, project_id: str = ""):
    return _env.search_tasks(query=query, project_id=project_id or None)


@app.get("/get_tasks_by_status")
def get_tasks_by_status(status: str, project_id: str = ""):
    return _env.get_tasks_by_status(status=status, project_id=project_id or None)


@app.get("/get_tasks_by_assignee")
def get_tasks_by_assignee(assignee_email: str, project_id: str = ""):
    return _env.get_tasks_by_assignee(assignee_email=assignee_email, project_id=project_id or None)


@app.get("/get_tasks_by_due_date")
def get_tasks_by_due_date(due_date: str, project_id: str = ""):
    return _env.get_tasks_by_due_date(due_date=due_date, project_id=project_id or None)


@app.get("/get_overdue_tasks")
def get_overdue_tasks(project_id: str = ""):
    return _env.get_overdue_tasks(project_id=project_id or None)


@app.get("/get_subtasks")
def get_subtasks(task_id: str):
    return _env.get_subtasks(task_id=task_id)


@app.get("/get_task_comments")
def get_task_comments(task_id: str):
    return _env.get_task_comments(task_id=task_id)


@app.get("/list_labels")
def list_labels():
    return _env.list_labels()


class CreateTaskRequest(BaseModel):
    title: str
    project_id: str
    description: Optional[str] = ""
    due_date: Optional[str] = ""
    priority: Optional[str] = "medium"
    assignee_email: Optional[str] = ""


@app.post("/create_task")
def create_task(req: CreateTaskRequest):
    return _env.create_task(title=req.title, project_id=req.project_id, description=req.description,
                             due_date=req.due_date, priority=req.priority, assignee_email=req.assignee_email)


class UpdateTaskStatusRequest(BaseModel):
    task_id: str
    status: str


@app.post("/update_task_status")
def update_task_status(req: UpdateTaskStatusRequest):
    return _env.update_task_status(task_id=req.task_id, status=req.status)


class UpdateTaskDetailsRequest(BaseModel):
    task_id: str
    title: Optional[str] = None
    description: Optional[str] = None


@app.post("/update_task_details")
def update_task_details(req: UpdateTaskDetailsRequest):
    return _env.update_task_details(task_id=req.task_id, title=req.title, description=req.description)


class AssignTaskRequest(BaseModel):
    task_id: str
    assignee_email: str


@app.post("/assign_task")
def assign_task(req: AssignTaskRequest):
    return _env.assign_task(task_id=req.task_id, assignee_email=req.assignee_email)


class SetDueDateRequest(BaseModel):
    task_id: str
    due_date: str


@app.post("/set_task_due_date")
def set_task_due_date(req: SetDueDateRequest):
    return _env.set_task_due_date(task_id=req.task_id, due_date=req.due_date)


class SetPriorityRequest(BaseModel):
    task_id: str
    priority: str


@app.post("/set_task_priority")
def set_task_priority(req: SetPriorityRequest):
    return _env.set_task_priority(task_id=req.task_id, priority=req.priority)


class AddSubtaskRequest(BaseModel):
    parent_task_id: str
    title: str


@app.post("/add_subtask")
def add_subtask(req: AddSubtaskRequest):
    return _env.add_subtask(parent_task_id=req.parent_task_id, title=req.title)


class AddCommentRequest(BaseModel):
    task_id: str
    content: str


@app.post("/add_comment_to_task")
def add_comment_to_task(req: AddCommentRequest):
    return _env.add_comment_to_task(task_id=req.task_id, content=req.content)


class LabelTaskRequest(BaseModel):
    task_id: str
    label_name: str


@app.post("/add_label_to_task")
def add_label_to_task(req: LabelTaskRequest):
    return _env.add_label_to_task(task_id=req.task_id, label_name=req.label_name)


@app.post("/remove_label_from_task")
def remove_label_from_task(req: LabelTaskRequest):
    return _env.remove_label_from_task(task_id=req.task_id, label_name=req.label_name)


class TaskIdRequest(BaseModel):
    task_id: str


@app.post("/delete_task")
def delete_task(req: TaskIdRequest):
    return _env.delete_task(task_id=req.task_id)


class CreateProjectRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    members: Optional[List[str]] = []


@app.post("/create_project")
def create_project(req: CreateProjectRequest):
    return _env.create_project(name=req.name, description=req.description, members=req.members)


class UpdateProjectRequest(BaseModel):
    project_id: str
    name: Optional[str] = None
    description: Optional[str] = None


@app.post("/update_project")
def update_project(req: UpdateProjectRequest):
    return _env.update_project(project_id=req.project_id, name=req.name, description=req.description)


class ProjectIdRequest(BaseModel):
    project_id: str


@app.post("/delete_project")
def delete_project(req: ProjectIdRequest):
    return _env.delete_project(project_id=req.project_id)


class ReorderTasksRequest(BaseModel):
    project_id: str
    task_ids_ordered: List[str]


@app.post("/reorder_tasks")
def reorder_tasks(req: ReorderTasksRequest):
    return _env.reorder_tasks(project_id=req.project_id, task_ids_ordered=req.task_ids_ordered)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=39206)
