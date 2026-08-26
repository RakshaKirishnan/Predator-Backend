"""
Database Seed Script: Inject Email Templates into MongoDB 'app_settings' collection.

Run:
  backend/.venv/bin/python3 backend/scripts/seed_email_templates.py
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(override=True)

MONGO_URI = os.getenv("FACE_AUTH_MONGO_URI", os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
MONGO_DB = os.getenv("FACE_AUTH_MONGO_DB", "predator")

# Exact template key format requested
EMAIL_TEMPLATES = [
    {
        "template_key": "registration",
        "name": "Registration Email Template",
        "Registration_email_template_subject": "You're invited — complete face signup",
        "Registration_email_template_body": """# You're invited to PREDATOR Console

Hi {{name}},

You have been invited to create your account using facial biometric authentication on the PREDATOR security platform.

<a href="{{invite_link}}" style="display: inline-block; padding: 12px 24px; background-color: #009669; color: #ffffff; text-decoration: none; border-radius: 9999px; font-weight: bold; font-family: sans-serif; box-shadow: 0 4px 12px rgba(0,150,105,0.3);">Accept Invitation & Register Face</a>

*This invitation link expires in {{expires_hours}} hours.*

If you did not expect this invitation, you can safely ignore this email.""",
        "Registration_email_template_placeholders": ["name", "email", "invite_link", "expires_hours"],
    },
    {
        "template_key": "warning",
        "name": "Warning Email Template",
        "Warning_email_template_subject": "⚠️ Security Alert — Multiple Failed Login Scans",
        "Warning_email_template_body": """# Security Warning Alert

Hi {{name}},

We detected multiple failed facial recognition login attempts on your account from IP address `{{ip_address}}` on {{timestamp}}.

<a href="#" style="display: inline-block; padding: 10px 20px; background-color: #dc2626; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: bold; font-family: sans-serif;">Report Security Breach</a>

*Security Protocol: PREDATOR Monitoring*""",
        "Warning_email_template_placeholders": ["name", "email", "ip_address", "timestamp"],
    },
    {
        "template_key": "welcome",
        "name": "Welcome Email Template",
        "Welcome_email_template_subject": "🎉 Welcome to PREDATOR — Facial Biometrics Enrolled",
        "Welcome_email_template_body": """# Welcome to PREDATOR Security

Hi {{name}},

Your facial biometric profile has been successfully enrolled and verified in the PREDATOR security system.

You can now log in seamlessly using face recognition.

<a href="{{dashboard_link}}" style="display: inline-block; padding: 12px 24px; background-color: #2563eb; color: #ffffff; text-decoration: none; border-radius: 8px; font-weight: bold; font-family: sans-serif;">Access Security Console</a>

*Role assigned: {{role}}*""",
        "Welcome_email_template_placeholders": ["name", "email", "role", "dashboard_link"],
    },
]


def seed_email_templates() -> None:
    print(f"Connecting to MongoDB at {MONGO_URI} (db: {MONGO_DB})...")
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[MONGO_DB]
    col_name = os.getenv("FACE_AUTH_APP_SETTINGS_COLLECTION", "app_settings")
    col = db[col_name]

    now = datetime.now(timezone.utc)
    doc = {
        "doc_type": "email_templates",
        "email_templates": EMAIL_TEMPLATES,
        "updated_at": now,
    }

    # Overwrite previous doc
    col.delete_many({"doc_type": "email_templates"})
    result = col.insert_one(doc)

    print(f"Successfully seeded {len(EMAIL_TEMPLATES)} email templates into 'app_settings' collection!")
    print(f"Inserted ID: {result.inserted_id}")
    client.close()


if __name__ == "__main__":
    seed_email_templates()
