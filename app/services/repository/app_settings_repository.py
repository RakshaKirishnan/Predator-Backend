"""App Settings repository for MongoDB 'app_settings' collection."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from app.db.mongo import MongoDB


from app.core.timezone import to_ist


class AppSettingsRepository:
    def __init__(self, mongo: MongoDB):
        self._col = mongo.app_settings

    def list_email_templates(self) -> dict[str, Any]:
        doc = self._col.find_one({"doc_type": "email_templates"}, {"_id": 0})
        if not doc or "email_templates" not in doc:
            
            try:
                
                doc = self._col.find_one({"doc_type": "email_templates"}, {"_id": 0})
            except Exception:
                pass

        now = datetime.now(timezone.utc)
        if not doc:
            return {
                "doc_type": "email_templates",
                "email_templates": [],
                "updated_at": to_ist(now),
                "is_customized": False,
            }

        updated_at = doc.get("updated_at")
        return {
            "doc_type": "email_templates",
            "email_templates": doc.get("email_templates", []),
            "updated_at": to_ist(updated_at or now),
            "is_customized": True,
        }

    def get_email_template_by_key(self, key_prefix: str) -> dict[str, Any]:
        templates_doc = self.list_email_templates()
        templates_list = templates_doc.get("email_templates", [])
        
        # Match by template_key or key_prefix
        prefix = key_prefix.capitalize()
        for t in templates_list:
            if (
                t.get("template_key") == key_prefix.lower()
                or f"{prefix}_email_template_subject" in t
                or key_prefix.lower() in str(t.get("name", "")).lower()
            ):
                subject_key = f"{prefix}_email_template_subject"
                body_key = f"{prefix}_email_template_body"
                placeholders_key = f"{prefix}_email_template_placeholders"
                return {
                    "template_key": t.get("template_key", key_prefix),
                    "name": t.get("name", f"{prefix} Email Template"),
                    "subject": t.get(subject_key) or t.get("subject", ""),
                    "body": t.get(body_key) or t.get("body", ""),
                    "placeholders": t.get(placeholders_key) or t.get("placeholders", []),
                }

        if templates_list:
            t0 = templates_list[0]
            return {
                "template_key": t0.get("template_key", "registration"),
                "name": t0.get("name", "Registration Email Template"),
                "subject": t0.get("Registration_email_template_subject", ""),
                "body": t0.get("Registration_email_template_body", ""),
                "placeholders": t0.get("Registration_email_template_placeholders", []),
            }

        return {
            "template_key": key_prefix,
            "name": f"{prefix} Email Template",
            "subject": "You're invited — complete face signup",
            "body": "",
            "placeholders": [],
        }

    def save_email_template(self, *, template_key: str, subject: str, body: str) -> dict[str, Any]:
        doc = self._col.find_one({"doc_type": "email_templates"}, {"_id": 0})
        templates = doc.get("email_templates", []) if doc else []

        prefix = template_key.capitalize()
        subject_key = f"{prefix}_email_template_subject"
        body_key = f"{prefix}_email_template_body"

        updated = False
        for t in templates:
            t_key = str(t.get("template_key", "")).lower()
            if t_key == template_key.lower() or subject_key in t or template_key.lower() in str(t.get("name", "")).lower():
                t[subject_key] = subject.strip()
                t[body_key] = body.strip()
                updated = True
                break

        if not updated:
            templates.append({
                "template_key": template_key.lower(),
                "name": f"{prefix} Email Template",
                subject_key: subject.strip(),
                body_key: body.strip(),
                f"{prefix}_email_template_placeholders": ["name", "email", "invite_link", "expires_hours"],
            })

        now = datetime.now(timezone.utc)
        payload = {
            "doc_type": "email_templates",
            "email_templates": templates,
            "updated_at": now,
        }
        self._col.update_one(
            {"doc_type": "email_templates"},
            {"$set": payload},
            upsert=True,
        )
        return self.list_email_templates()


def render_markdown_to_html(markdown_text: str, context: dict[str, Any]) -> str:
    """Render markdown text with template variables into clean HTML for emails."""
    text = markdown_text
    for key, value in context.items():
        text = text.replace(f"{{{{{key}}}}}", str(value))

    # Convert Markdown headings
    text = re.sub(r"^# (.*?)$", r'<h2 style="color: #0f172a; font-family: sans-serif; margin-top: 0;">\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r"^## (.*?)$", r'<h3 style="color: #1e293b; font-family: sans-serif;">\1</h3>', text, flags=re.MULTILINE)

    # Convert Markdown buttons/links: [Text](url)
    def link_replacer(match):
        label, url = match.group(1), match.group(2)
        if "Accept" in label or "Register" in label or "Click" in label or "Access" in label:
            return f'''<p style="margin: 1.2rem 0;"><a href="{url}" style="display: inline-block; padding: 12px 24px; background-color: #009669; color: #ffffff; text-decoration: none; border-radius: 9999px; font-weight: bold; font-family: sans-serif; box-shadow: 0 4px 12px rgba(0,150,105,0.3);">{label}</a></p>'''
        return f'<a href="{url}" style="color: #009669; font-weight: 600;">{label}</a>'

    text = re.sub(r"\[(.*?)\]\((.*?)\)", link_replacer, text)

    # Convert Markdown bold and italic
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)

    # Convert linebreaks to paragraphs/br if not raw html tag
    paragraphs = text.split("\n\n")
    html_paragraphs = []
    for p in paragraphs:
        p_clean = p.strip().replace("\n", "<br>")
        if p_clean.startswith("<h2") or p_clean.startswith("<h3") or p_clean.startswith("<p") or p_clean.startswith("<a") or p_clean.startswith("<div"):
            html_paragraphs.append(p_clean)
        else:
            html_paragraphs.append(f'<p style="margin: 0.6rem 0; color: #334155; font-size: 0.92rem; line-height: 1.5;">{p_clean}</p>')

    html_body = "\n".join(html_paragraphs)

    return f"""
    <div style="max-width: 560px; margin: 0 auto; padding: 2rem; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 10px 25px rgba(0,0,0,0.05);">
        {html_body}
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin-top: 2rem; margin-bottom: 1rem;" />
        <p style="color: #94a3b8; font-size: 0.75rem; text-align: center; margin: 0;">
            Sent by PREDATOR Face Auth System &bull; Secure Biometric Security Console
        </p>
    </div>
    """
