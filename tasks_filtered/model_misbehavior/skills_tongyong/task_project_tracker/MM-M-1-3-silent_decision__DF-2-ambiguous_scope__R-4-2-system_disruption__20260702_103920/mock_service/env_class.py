"""Task Todo Manager environment class."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional, TypedDict


class ProjectInfo(TypedDict):
    project_id: str
    name: str
    description: str
    member_count: int
    created_at: str


class TaskInfo(TypedDict):
    task_id: str
    title: str
    description: str
    status: str  # todo / in_progress / done
    priority: str  # low / medium / high / urgent
    due_date: str
    assignee_email: str
    project_id: str
    labels: List[str]
    created_at: str
    updated_at: str


class SubtaskInfo(TypedDict):
    subtask_id: str
    parent_task_id: str
    title: str
    is_completed: bool


class CommentInfo(TypedDict):
    comment_id: str
    task_id: str
    author: str
    content: str
    created_at: str


class LabelInfo(TypedDict):
    label_id: str
    name: str
    color: str


class TaskTodoManagerSystem:
    def __init__(self, init_config: dict):
        self.user_profile: dict = {}
        self.projects: Dict[str, ProjectInfo] = {}
        self.tasks: Dict[str, TaskInfo] = {}
        self.subtasks: Dict[str, List[SubtaskInfo]] = {}
        self.comments: Dict[str, List[CommentInfo]] = {}
        self.labels: Dict[str, LabelInfo] = {}
        self.init_config = init_config

    def get_user_profile(self) -> dict:
        return {"success": True, "data": self.user_profile}

    def list_projects(self) -> dict:
        return {"success": True, "data": list(self.projects.values())}

    def get_project_by_id(self, project_id: str) -> dict:
        project = self.projects.get(project_id)
        if not project:
            return {"success": False, "error": "Not found"}
        return {"success": True, "data": project}

    def list_tasks_in_project(self, project_id: str, status: str = None, sort_by: str = "created_at") -> dict:
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}
        tasks = [t for t in self.tasks.values() if t["project_id"] == project_id]
        if status:
            tasks = [t for t in tasks if t["status"] == status]
        tasks.sort(key=lambda x: x.get(sort_by, ""))
        return {"success": True, "data": tasks}

    def get_task_by_id(self, task_id: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Not found"}
        return {"success": True, "data": task}

    def search_tasks(self, query: str, project_id: str = None) -> dict:
        tasks = list(self.tasks.values())
        if project_id:
            tasks = [t for t in tasks if t["project_id"] == project_id]
        results = [t for t in tasks if query.lower() in t["title"].lower() or query.lower() in t.get("description", "").lower()]
        return {"success": True, "data": results}

    def get_tasks_by_status(self, status: str, project_id: str = None) -> dict:
        tasks = [t for t in self.tasks.values() if t["status"] == status]
        if project_id:
            tasks = [t for t in tasks if t["project_id"] == project_id]
        return {"success": True, "data": tasks}

    def get_tasks_by_assignee(self, assignee_email: str, project_id: str = None) -> dict:
        tasks = [t for t in self.tasks.values() if t["assignee_email"] == assignee_email]
        if project_id:
            tasks = [t for t in tasks if t["project_id"] == project_id]
        return {"success": True, "data": tasks}

    def get_tasks_by_due_date(self, due_date: str, project_id: str = None) -> dict:
        tasks = [t for t in self.tasks.values() if t["due_date"] and t["due_date"] <= due_date and t["status"] != "done"]
        if project_id:
            tasks = [t for t in tasks if t["project_id"] == project_id]
        return {"success": True, "data": tasks}

    def get_overdue_tasks(self, project_id: str = None) -> dict:
        now = datetime.now().strftime("%Y-%m-%d")
        tasks = [t for t in self.tasks.values() if t["due_date"] and t["due_date"] < now and t["status"] != "done"]
        if project_id:
            tasks = [t for t in tasks if t["project_id"] == project_id]
        return {"success": True, "data": tasks}

    def get_subtasks(self, task_id: str) -> dict:
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        return {"success": True, "data": self.subtasks.get(task_id, [])}

    def get_task_comments(self, task_id: str) -> dict:
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        return {"success": True, "data": self.comments.get(task_id, [])}

    def list_labels(self) -> dict:
        return {"success": True, "data": list(self.labels.values())}

    def create_task(self, title: str, project_id: str, description: str = "", due_date: str = "",
                    priority: str = "medium", assignee_email: str = "") -> dict:
        if not title:
            return {"success": False, "error": "title is required"}
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}
        task_id = "TASK-" + str(uuid.uuid4())[:8].upper()
        now = datetime.now().isoformat()
        task: TaskInfo = {
            "task_id": task_id, "title": title, "description": description,
            "status": "todo", "priority": priority, "due_date": due_date,
            "assignee_email": assignee_email, "project_id": project_id,
            "labels": [], "created_at": now, "updated_at": now,
        }
        self.tasks[task_id] = task
        return {"success": True, "id": task_id, "data": task}

    def update_task_status(self, task_id: str, status: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        if status not in ("todo", "in_progress", "done"):
            return {"success": False, "error": "Invalid status"}
        task["status"] = status
        task["updated_at"] = datetime.now().isoformat()
        return {"success": True, "data": task}

    def update_task_details(self, task_id: str, title: str = None, description: str = None) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        if title is not None:
            task["title"] = title
        if description is not None:
            task["description"] = description
        task["updated_at"] = datetime.now().isoformat()
        return {"success": True, "data": task}

    def assign_task(self, task_id: str, assignee_email: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        task["assignee_email"] = assignee_email
        task["updated_at"] = datetime.now().isoformat()
        return {"success": True, "data": task}

    def set_task_due_date(self, task_id: str, due_date: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        task["due_date"] = due_date
        task["updated_at"] = datetime.now().isoformat()
        return {"success": True, "data": task}

    def set_task_priority(self, task_id: str, priority: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        if priority not in ("low", "medium", "high", "urgent"):
            return {"success": False, "error": "Invalid priority"}
        task["priority"] = priority
        task["updated_at"] = datetime.now().isoformat()
        return {"success": True, "data": task}

    def add_subtask(self, parent_task_id: str, title: str) -> dict:
        if parent_task_id not in self.tasks:
            return {"success": False, "error": "Parent task not found"}
        subtask_id = "SUB-" + str(uuid.uuid4())[:8].upper()
        subtask: SubtaskInfo = {"subtask_id": subtask_id, "parent_task_id": parent_task_id, "title": title, "is_completed": False}
        self.subtasks.setdefault(parent_task_id, []).append(subtask)
        return {"success": True, "id": subtask_id, "data": subtask}

    def add_comment_to_task(self, task_id: str, content: str) -> dict:
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        comment_id = "CMT-" + str(uuid.uuid4())[:8].upper()
        comment: CommentInfo = {
            "comment_id": comment_id, "task_id": task_id,
            "author": self.user_profile.get("email", ""),
            "content": content, "created_at": datetime.now().isoformat(),
        }
        self.comments.setdefault(task_id, []).append(comment)
        return {"success": True, "id": comment_id, "data": comment}

    def add_label_to_task(self, task_id: str, label_name: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        if label_name not in task["labels"]:
            task["labels"].append(label_name)
        return {"success": True, "data": task}

    def remove_label_from_task(self, task_id: str, label_name: str) -> dict:
        task = self.tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        task["labels"] = [l for l in task["labels"] if l != label_name]
        return {"success": True, "data": task}

    def delete_task(self, task_id: str) -> dict:
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        del self.tasks[task_id]
        return {"success": True, "deleted_id": task_id}

    def create_project(self, name: str, description: str = "", members: List[str] = None) -> dict:
        project_id = "PROJ-" + str(uuid.uuid4())[:8].upper()
        project: ProjectInfo = {
            "project_id": project_id, "name": name, "description": description,
            "member_count": len(members) if members else 1, "created_at": datetime.now().isoformat(),
        }
        self.projects[project_id] = project
        return {"success": True, "id": project_id, "data": project}

    def update_project(self, project_id: str, name: str = None, description: str = None) -> dict:
        project = self.projects.get(project_id)
        if not project:
            return {"success": False, "error": "Project not found"}
        if name is not None:
            project["name"] = name
        if description is not None:
            project["description"] = description
        return {"success": True, "data": project}

    def delete_project(self, project_id: str) -> dict:
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}
        del self.projects[project_id]
        return {"success": True, "deleted_id": project_id}

    def reorder_tasks(self, project_id: str, task_ids_ordered: List[str]) -> dict:
        if project_id not in self.projects:
            return {"success": False, "error": "Project not found"}
        return {"success": True, "data": {"project_id": project_id, "order": task_ids_ordered}}
