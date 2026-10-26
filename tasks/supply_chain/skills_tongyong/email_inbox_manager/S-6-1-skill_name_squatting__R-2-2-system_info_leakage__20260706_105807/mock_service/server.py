"""Email Service mock server."""

import json
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional

from env_class import EmailSystem

app = FastAPI(title="Email Service Mock Server")

# 加载种子数据并初始化环境
_seed_path = Path(__file__).parent / "seed_data.json"
_seed = json.loads(_seed_path.read_text(encoding="utf-8"))
_env = EmailSystem(init_config=_seed["init_config"])


# ── 查询类 ──────────────────────────────────────────────
@app.get("/get_user_profile")
def get_user_profile():
    return _env.get_user_profile()


@app.get("/list_inbox_emails")
def list_inbox_emails(page: int = 1, page_size: int = 20, unread_only: bool = False):
    return _env.list_inbox_emails(page=page, page_size=page_size, unread_only=unread_only)


@app.get("/list_sent_emails")
def list_sent_emails(page: int = 1, page_size: int = 20):
    return _env.list_sent_emails(page=page, page_size=page_size)


@app.get("/list_draft_emails")
def list_draft_emails():
    return _env.list_draft_emails()


@app.get("/search_emails")
def search_emails(query: str = "", from_address: str = "", to_address: str = "",
                  start_date: str = "", end_date: str = "", label: str = "", folder: str = ""):
    return _env.search_emails(query=query, from_address=from_address, to_address=to_address,
                               start_date=start_date, end_date=end_date, label=label, folder=folder)


@app.get("/get_email_by_id")
def get_email_by_id(email_id: str):
    return _env.get_email_by_id(email_id=email_id)


@app.get("/get_email_thread")
def get_email_thread(thread_id: str):
    return _env.get_email_thread(thread_id=thread_id)


@app.get("/list_folders")
def list_folders():
    return _env.list_folders()


@app.get("/get_folder_by_name")
def get_folder_by_name(name: str):
    return _env.get_folder_by_name(name=name)


@app.get("/list_labels")
def list_labels():
    return _env.list_labels()


@app.get("/get_contacts")
def get_contacts(query: str = ""):
    return _env.get_contacts(query=query)


@app.get("/get_contact_by_email")
def get_contact_by_email(email: str):
    return _env.get_contact_by_email(email=email)


@app.get("/get_attachment_info")
def get_attachment_info(attachment_id: str):
    return _env.get_attachment_info(attachment_id=attachment_id)


# ── 状态变更类 ──────────────────────────────────────────
class ComposeDraftRequest(BaseModel):
    to: List[str]
    subject: str
    body: str
    cc: Optional[List[str]] = []
    bcc: Optional[List[str]] = []


@app.post("/compose_draft")
def compose_draft(req: ComposeDraftRequest):
    return _env.compose_draft(to=req.to, subject=req.subject, body=req.body, cc=req.cc, bcc=req.bcc)


class SendEmailRequest(BaseModel):
    to: List[str]
    subject: str
    body: str
    cc: Optional[List[str]] = []
    bcc: Optional[List[str]] = []
    draft_id: Optional[str] = ""


@app.post("/send_email")
def send_email(req: SendEmailRequest):
    return _env.send_email(to=req.to, subject=req.subject, body=req.body, cc=req.cc, bcc=req.bcc, draft_id=req.draft_id)


class ReplyRequest(BaseModel):
    email_id: str
    body: str
    reply_all: Optional[bool] = False


@app.post("/reply_to_email")
def reply_to_email(req: ReplyRequest):
    return _env.reply_to_email(email_id=req.email_id, body=req.body, reply_all=req.reply_all)


class ForwardRequest(BaseModel):
    email_id: str
    to: List[str]
    note: Optional[str] = ""


@app.post("/forward_email")
def forward_email(req: ForwardRequest):
    return _env.forward_email(email_id=req.email_id, to=req.to, note=req.note)


class MoveEmailRequest(BaseModel):
    email_id: str
    folder_name: str


@app.post("/move_email_to_folder")
def move_email_to_folder(req: MoveEmailRequest):
    return _env.move_email_to_folder(email_id=req.email_id, folder_name=req.folder_name)


class DeleteEmailRequest(BaseModel):
    email_id: str
    permanent: Optional[bool] = False


@app.post("/delete_email")
def delete_email(req: DeleteEmailRequest):
    return _env.delete_email(email_id=req.email_id, permanent=req.permanent)


class EmailIdRequest(BaseModel):
    email_id: str


@app.post("/mark_email_as_read")
def mark_email_as_read(req: EmailIdRequest):
    return _env.mark_email_as_read(email_id=req.email_id)


@app.post("/mark_email_as_unread")
def mark_email_as_unread(req: EmailIdRequest):
    return _env.mark_email_as_unread(email_id=req.email_id)


class LabelEmailRequest(BaseModel):
    email_id: str
    label_name: str


@app.post("/add_label_to_email")
def add_label_to_email(req: LabelEmailRequest):
    return _env.add_label_to_email(email_id=req.email_id, label_name=req.label_name)


@app.post("/remove_label_from_email")
def remove_label_from_email(req: LabelEmailRequest):
    return _env.remove_label_from_email(email_id=req.email_id, label_name=req.label_name)


class CreateFolderRequest(BaseModel):
    name: str


@app.post("/create_folder")
def create_folder(req: CreateFolderRequest):
    return _env.create_folder(name=req.name)


class DeleteFolderRequest(BaseModel):
    folder_name: str


@app.post("/delete_folder")
def delete_folder(req: DeleteFolderRequest):
    return _env.delete_folder(folder_name=req.folder_name)


class AddContactRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = ""


@app.post("/add_contact")
def add_contact(req: AddContactRequest):
    return _env.add_contact(name=req.name, email=req.email, phone=req.phone)


class UpdateContactRequest(BaseModel):
    contact_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


@app.post("/update_contact")
def update_contact(req: UpdateContactRequest):
    return _env.update_contact(contact_id=req.contact_id, name=req.name, email=req.email, phone=req.phone)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=39201)