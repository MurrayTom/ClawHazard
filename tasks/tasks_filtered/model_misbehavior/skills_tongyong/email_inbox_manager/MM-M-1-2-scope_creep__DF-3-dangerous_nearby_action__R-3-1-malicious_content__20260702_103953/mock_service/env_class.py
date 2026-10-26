"""Email Service environment class."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class EmailSystem:
    def __init__(self, init_config: Dict[str, Any]):
        self.user_profile: Dict = init_config.get("user_profile", {})
        self.emails: Dict[str, Dict] = init_config.get("emails", {})
        self.folders: Dict[str, Dict] = init_config.get("folders", {})
        self.labels: Dict[str, Dict] = init_config.get("labels", {})
        self.contacts: Dict[str, Dict] = init_config.get("contacts", {})
        self.attachments: Dict[str, Dict] = init_config.get("attachments", {})

    def _ok(self, data):
        return {"success": True, "data": data}

    def _not_found(self, msg="Not found"):
        return {"success": False, "error": msg}

    def _new_id(self, prefix=""):
        return f"{prefix}{uuid.uuid4().hex[:8].upper()}"

    # ── 查询类 ──────────────────────────────────────────
    def get_user_profile(self):
        return self._ok(self.user_profile)

    def list_inbox_emails(self, page=1, page_size=20, unread_only=False):
        items = [e for e in self.emails.values() if e.get("folder") == "inbox"]
        if unread_only:
            items = [e for e in items if not e.get("is_read", False)]
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        start = (page - 1) * page_size
        return self._ok(items[start:start + page_size])

    def list_sent_emails(self, page=1, page_size=20):
        items = [e for e in self.emails.values() if e.get("folder") == "sent"]
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        start = (page - 1) * page_size
        return self._ok(items[start:start + page_size])

    def list_draft_emails(self):
        items = [e for e in self.emails.values() if e.get("folder") == "drafts"]
        return self._ok(items)

    def search_emails(self, query="", from_address="", to_address="", start_date="", end_date="", label="", folder=""):
        results = list(self.emails.values())
        if query:
            results = [e for e in results if query.lower() in e.get("subject", "").lower() or query.lower() in e.get("body", "").lower()]
        if from_address:
            results = [e for e in results if from_address.lower() in e.get("from", "").lower()]
        if to_address:
            results = [e for e in results if any(to_address.lower() in t.lower() for t in e.get("to", []))]
        if label:
            results = [e for e in results if label in e.get("labels", [])]
        if folder:
            results = [e for e in results if e.get("folder") == folder]
        return self._ok(results)

    def get_email_by_id(self, email_id: str):
        email = self.emails.get(email_id)
        if not email:
            return self._not_found()
        return self._ok(email)

    def get_email_thread(self, thread_id: str):
        items = [e for e in self.emails.values() if e.get("thread_id") == thread_id]
        if not items:
            return self._not_found()
        items.sort(key=lambda x: x.get("timestamp", ""))
        return self._ok(items)

    def list_folders(self):
        return self._ok(list(self.folders.values()))

    def get_folder_by_name(self, name: str):
        for f in self.folders.values():
            if f.get("name") == name:
                return self._ok(f)
        return self._not_found()

    def list_labels(self):
        return self._ok(list(self.labels.values()))

    def get_contacts(self, query=""):
        items = list(self.contacts.values())
        if query:
            items = [c for c in items if query.lower() in c.get("name", "").lower() or query.lower() in c.get("email", "").lower()]
        return self._ok(items)

    def get_contact_by_email(self, email: str):
        for c in self.contacts.values():
            if c.get("email", "").lower() == email.lower():
                return self._ok(c)
        return self._not_found()

    def get_attachment_info(self, attachment_id: str):
        att = self.attachments.get(attachment_id)
        if not att:
            return self._not_found()
        return self._ok(att)

    # ── 状态变更类 ──────────────────────────────────────
    def compose_draft(self, to: List[str], subject: str, body: str, cc=None, bcc=None):
        draft_id = self._new_id("DRAFT-")
        draft = {
            "email_id": draft_id,
            "from": self.user_profile.get("email", ""),
            "to": to,
            "cc": cc or [],
            "bcc": bcc or [],
            "subject": subject,
            "body": body,
            "timestamp": datetime.now().isoformat(),
            "is_read": True,
            "folder": "drafts",
            "labels": [],
            "thread_id": draft_id
        }
        self.emails[draft_id] = draft
        return {"success": True, "id": draft_id, "data": draft}

    def send_email(self, to: List[str], subject: str, body: str, cc=None, bcc=None, draft_id=""):
        if draft_id and draft_id in self.emails:
            del self.emails[draft_id]
        email_id = self._new_id("EMAIL-")
        email = {
            "email_id": email_id,
            "from": self.user_profile.get("email", ""),
            "to": to,
            "cc": cc or [],
            "bcc": bcc or [],
            "subject": subject,
            "body": body,
            "timestamp": datetime.now().isoformat(),
            "is_read": True,
            "folder": "sent",
            "labels": [],
            "thread_id": email_id
        }
        self.emails[email_id] = email
        return {"success": True, "id": email_id, "timestamp": email["timestamp"]}

    def reply_to_email(self, email_id: str, body: str, reply_all=False):
        original = self.emails.get(email_id)
        if not original:
            return self._not_found()
        reply_id = self._new_id("EMAIL-")
        reply = {
            "email_id": reply_id,
            "from": self.user_profile.get("email", ""),
            "to": [original.get("from", "")],
            "subject": f"Re: {original.get('subject', '')}",
            "body": body,
            "timestamp": datetime.now().isoformat(),
            "is_read": True,
            "folder": "sent",
            "labels": [],
            "thread_id": original.get("thread_id", email_id)
        }
        self.emails[reply_id] = reply
        return {"success": True, "id": reply_id, "timestamp": reply["timestamp"]}

    def forward_email(self, email_id: str, to: List[str], note=""):
        original = self.emails.get(email_id)
        if not original:
            return self._not_found()
        fwd_id = self._new_id("EMAIL-")
        fwd = {
            "email_id": fwd_id,
            "from": self.user_profile.get("email", ""),
            "to": to,
            "subject": f"Fwd: {original.get('subject', '')}",
            "body": f"{note}\n\n--- 转发邮件 ---\n{original.get('body', '')}",
            "timestamp": datetime.now().isoformat(),
            "is_read": True,
            "folder": "sent",
            "labels": [],
            "thread_id": fwd_id
        }
        self.emails[fwd_id] = fwd
        return {"success": True, "id": fwd_id, "timestamp": fwd["timestamp"]}

    def move_email_to_folder(self, email_id: str, folder_name: str):
        email = self.emails.get(email_id)
        if not email:
            return self._not_found()
        email["folder"] = folder_name
        return self._ok(email)

    def delete_email(self, email_id: str, permanent=False):
        email = self.emails.get(email_id)
        if not email:
            return self._not_found()
        if permanent or email.get("folder") == "trash":
            del self.emails[email_id]
        else:
            email["folder"] = "trash"
        return {"success": True, "deleted_id": email_id}

    def mark_email_as_read(self, email_id: str):
        email = self.emails.get(email_id)
        if not email:
            return self._not_found()
        email["is_read"] = True
        return self._ok(email)

    def mark_email_as_unread(self, email_id: str):
        email = self.emails.get(email_id)
        if not email:
            return self._not_found()
        email["is_read"] = False
        return self._ok(email)

    def add_label_to_email(self, email_id: str, label_name: str):
        email = self.emails.get(email_id)
        if not email:
            return self._not_found()
        if label_name not in email.get("labels", []):
            email.setdefault("labels", []).append(label_name)
        return self._ok(email)

    def remove_label_from_email(self, email_id: str, label_name: str):
        email = self.emails.get(email_id)
        if not email:
            return self._not_found()
        email["labels"] = [l for l in email.get("labels", []) if l != label_name]
        return self._ok(email)

    def create_folder(self, name: str):
        folder_id = self._new_id("FOLDER-")
        folder = {"folder_id": folder_id, "name": name, "email_count": 0}
        self.folders[folder_id] = folder
        return {"success": True, "id": folder_id, "data": folder}

    def delete_folder(self, folder_name: str):
        for fid, f in list(self.folders.items()):
            if f.get("name") == folder_name:
                del self.folders[fid]
                return {"success": True, "deleted_id": fid}
        return self._not_found()

    def add_contact(self, name: str, email: str, phone=""):
        contact_id = self._new_id("CONTACT-")
        contact = {"contact_id": contact_id, "name": name, "email": email, "phone": phone}
        self.contacts[contact_id] = contact
        return {"success": True, "id": contact_id, "data": contact}

    def update_contact(self, contact_id: str, name=None, email=None, phone=None):
        contact = self.contacts.get(contact_id)
        if not contact:
            return self._not_found()
        if name is not None:
            contact["name"] = name
        if email is not None:
            contact["email"] = email
        if phone is not None:
            contact["phone"] = phone
        return self._ok(contact)