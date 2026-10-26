"""Mock Address Book Contact API service (FastAPI)."""

from __future__ import annotations

import json
import copy
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

# 将 env_class.py 所在目录加入 sys.path
_SKILL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL_DIR))

from env_class import PersonalContactsManagementSystem  # noqa: E402

app = FastAPI(title="Mock Address Book Contact API")

# ── 种子数据路径 ──────────────────────────────────────────────────────────────
FIXTURES_PATH = Path(os.environ.get(
    "ADDRESS_BOOK_CONTACT_FIXTURES",
    str(_SKILL_DIR / "env_185_rl-task_1_injected.json"),
))

_env: PersonalContactsManagementSystem | None = None
_audit_log: list[dict[str, Any]] = []


def _load_fixtures() -> None:
    global _env
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    # init_config 可能嵌套在 "init_config" 键下，也可能直接是顶层
    init_cfg = raw.get("init_config", raw)
    _env = PersonalContactsManagementSystem(init_config=init_cfg)
    # 将 init_config 中的各实体加载到环境实例
    for attr, val in init_cfg.items():
        if hasattr(_env, attr) and isinstance(val, dict):
            setattr(_env, attr, val)
        elif hasattr(_env, attr) and isinstance(val, list):
            setattr(_env, attr, val)


_load_fixtures()


def _log_call(endpoint: str, request_body: dict[str, Any], response_body: Any) -> None:
    _audit_log.append({
        "endpoint": endpoint,
        "request_body": request_body,
        "response_body": response_body,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ── 通用调用端点 ──────────────────────────────────────────────────────────────

class CallRequest(BaseModel):
    operation: str
    params: dict[str, Any] = {}


@app.post("/address_book_contact/call")
def call_operation(req: CallRequest) -> dict[str, Any]:
    """通用操作调用端点：传入 operation 名称和 params 字典"""
    if _env is None:
        return {"success": False, "error": "Environment not initialized"}
    method = getattr(_env, req.operation, None)
    if method is None:
        resp = {"success": False, "error": f"Unknown operation: {req.operation}"}
        _log_call(f"/address_book_contact/call", req.model_dump(), resp)
        return resp
    try:
        resp = method(**req.params)
    except TypeError as e:
        resp = {"success": False, "error": f"Parameter error: {e}"}
    _log_call(f"/address_book_contact/call", req.model_dump(), resp)
    return resp


# ── 各操作独立端点 ────────────────────────────────────────────────────────────

@app.post("/address_book_contact/list_all_contacts")
def endpoint_list_all_contacts() -> dict[str, Any]:
    """Retrieve the full list of contacts in the address book."""
    resp = _env.list_all_contacts()
    _log_call("/address_book_contact/list_all_contacts", {}, resp)
    return resp


class GetContactByIdRequest(BaseModel):
    contact_id: str

@app.post("/address_book_contact/get_contact_by_id")
def endpoint_get_contact_by_id(req: GetContactByIdRequest) -> dict[str, Any]:
    """Fetch detailed information for a specific contact given contact_id."""
    resp = _env.get_contact_by_id(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/get_contact_by_id", req.model_dump(), resp)
    return resp


class GetContactsByNameRequest(BaseModel):
    name: str

@app.post("/address_book_contact/get_contacts_by_name")
def endpoint_get_contacts_by_name(req: GetContactsByNameRequest) -> dict[str, Any]:
    """Fetch all contacts matching a given name (including possible duplicates)."""
    resp = _env.get_contacts_by_name(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/get_contacts_by_name", req.model_dump(), resp)
    return resp


class FilterContactsByCategoryRequest(BaseModel):
    category_id: str | None = None
    category_name: str | None = None

@app.post("/address_book_contact/filter_contacts_by_category")
def endpoint_filter_contacts_by_category(req: FilterContactsByCategoryRequest) -> dict[str, Any]:
    """Retrieve contacts associated with a particular category (by category_id or category_name)."""
    resp = _env.filter_contacts_by_category(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/filter_contacts_by_category", req.model_dump(), resp)
    return resp


class GetContactsByTypeRequest(BaseModel):
    contact_type: str

@app.post("/address_book_contact/get_contacts_by_type")
def endpoint_get_contacts_by_type(req: GetContactsByTypeRequest) -> dict[str, Any]:
    """Fetch contacts by their type (individual or institution)."""
    resp = _env.get_contacts_by_type(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/get_contacts_by_type", req.model_dump(), resp)
    return resp


class GetContactCategoriesRequest(BaseModel):
    contact_id: str

@app.post("/address_book_contact/get_contact_categories")
def endpoint_get_contact_categories(req: GetContactCategoriesRequest) -> dict[str, Any]:
    """List all categories assigned to a contact."""
    resp = _env.get_contact_categories(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/get_contact_categories", req.model_dump(), resp)
    return resp


@app.post("/address_book_contact/list_all_categories")
def endpoint_list_all_categories() -> dict[str, Any]:
    """Retrieve all category definitions available (name, description, id)."""
    resp = _env.list_all_categories()
    _log_call("/address_book_contact/list_all_categories", {}, resp)
    return resp


class GetCategoryByNameRequest(BaseModel):
    category_name: str

@app.post("/address_book_contact/get_category_by_name")
def endpoint_get_category_by_name(req: GetCategoryByNameRequest) -> dict[str, Any]:
    """Lookup a category's attributes using its name."""
    resp = _env.get_category_by_name(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/get_category_by_name", req.model_dump(), resp)
    return resp


class AddContactRequest(BaseModel):
    contact_id: str
    name: str
    type: str
    phone_numbers: list
    addresses: list | None = None
    emails: list | None = None
    notes: str = ""
    categories: list | None = None

@app.post("/address_book_contact/add_contact")
def endpoint_add_contact(req: AddContactRequest) -> dict[str, Any]:
    """Add a new contact record to the address book."""
    resp = _env.add_contact(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/add_contact", req.model_dump(), resp)
    return resp


class UpdateContactInfoRequest(BaseModel):
    contact_id: str
    name: str | None = None
    type: str | None = None
    phone_numbers: list[str] | None = None
    addresses: list[str] | None = None
    emails: list[str] | None = None
    notes: str | None = None
    categories: list[str] | None = None

@app.post("/address_book_contact/update_contact_info")
def endpoint_update_contact_info(req: UpdateContactInfoRequest) -> dict[str, Any]:
    """Edit the information (phones, addresses, emails, notes, categories) of an existing contact."""
    resp = _env.update_contact_info(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/update_contact_info", req.model_dump(), resp)
    return resp


class AddCategoryToContactRequest(BaseModel):
    contact_id: str
    category_id: str

@app.post("/address_book_contact/add_category_to_contact")
def endpoint_add_category_to_contact(req: AddCategoryToContactRequest) -> dict[str, Any]:
    """Assign an existing category to a contact."""
    resp = _env.add_category_to_contact(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/add_category_to_contact", req.model_dump(), resp)
    return resp


class RemoveCategoryFromContactRequest(BaseModel):
    contact_id: str
    category_id: str

@app.post("/address_book_contact/remove_category_from_contact")
def endpoint_remove_category_from_contact(req: RemoveCategoryFromContactRequest) -> dict[str, Any]:
    """Unassign a category from a contact."""
    resp = _env.remove_category_from_contact(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/remove_category_from_contact", req.model_dump(), resp)
    return resp


class DeleteContactRequest(BaseModel):
    contact_id: str

@app.post("/address_book_contact/delete_contact")
def endpoint_delete_contact(req: DeleteContactRequest) -> dict[str, Any]:
    """Permanently remove a contact record from the system (irreversible unless undo is implemented)."""
    resp = _env.delete_contact(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/delete_contact", req.model_dump(), resp)
    return resp


class UndoDeleteContactRequest(BaseModel):
    contact_id: str

@app.post("/address_book_contact/undo_delete_contact")
def endpoint_undo_delete_contact(req: UndoDeleteContactRequest) -> dict[str, Any]:
    """Restore a previously deleted contact (if undo feature is supported)."""
    resp = _env.undo_delete_contact(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/undo_delete_contact", req.model_dump(), resp)
    return resp


class AddCategoryRequest(BaseModel):
    category_id: str
    category_name: str
    description: str

@app.post("/address_book_contact/add_category")
def endpoint_add_category(req: AddCategoryRequest) -> dict[str, Any]:
    """Create a new category in the address book."""
    resp = _env.add_category(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/add_category", req.model_dump(), resp)
    return resp


class UpdateCategoryInfoRequest(BaseModel):
    category_id: str
    category_name: str | None = None
    description: str | None = None

@app.post("/address_book_contact/update_category_info")
def endpoint_update_category_info(req: UpdateCategoryInfoRequest) -> dict[str, Any]:
    """Change the name or description of an existing category."""
    resp = _env.update_category_info(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/update_category_info", req.model_dump(), resp)
    return resp


class DeleteCategoryRequest(BaseModel):
    category_id: str

@app.post("/address_book_contact/delete_category")
def endpoint_delete_category(req: DeleteCategoryRequest) -> dict[str, Any]:
    """Remove a category from the address book (and/or unassign it from any contacts)."""
    resp = _env.delete_category(**req.model_dump(exclude_none=True))
    _log_call("/address_book_contact/delete_category", req.model_dump(), resp)
    return resp


# ── 审计 / 重置 ───────────────────────────────────────────────────────────────

@app.get("/address_book_contact/audit")
def get_audit() -> dict[str, Any]:
    return {"calls": _audit_log}


@app.post("/address_book_contact/reset")
def reset_state() -> dict[str, str]:
    global _audit_log
    _audit_log = []
    _load_fixtures()
    return {"status": "reset"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9325")))
