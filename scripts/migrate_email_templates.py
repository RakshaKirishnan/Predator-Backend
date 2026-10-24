#!/usr/bin/env python3
"""
Migrate Email Templates from Local MongoDB to Docker MongoDB.

This script extracts ONLY the email templates ('doc_type': 'email_templates')
from the local MongoDB 'app_settings' collection and transfers them directly
into the Docker MongoDB container ('predator-mongo').

Usage:
  # From project root:
  backend/.venv/bin/python3 backend/scripts/migrate_email_templates.py

Options / Environment variables:
  SOURCE_MONGO_URI : Source MongoDB URI (default: mongodb://localhost:27017)
  SOURCE_MONGO_DB  : Source DB name (default: predator)
  DOCKER_CONTAINER : Target Mongo Docker container name (default: predator-mongo)
  DEST_MONGO_DB    : Target DB name (default: predator)
  DEST_MONGO_URI   : (Optional) Target MongoDB URI if host-accessible
  --dry-run        : Preview what will be migrated without writing
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from bson import json_util
from pymongo import MongoClient


def migrate_templates(
    source_uri: str,
    source_db_name: str,
    dest_container: str,
    dest_db_name: str,
    dest_uri: str | None = None,
    dry_run: bool = False,
) -> None:
    print("=" * 60)
    print("  EMAIL TEMPLATES MIGRATION: Local Mongo -> Docker Mongo")
    print("=" * 60)
    print(f"Source: {source_uri} (DB: {source_db_name})")
    if dest_uri:
        print(f"Destination URI: {dest_uri} (DB: {dest_db_name})")
    else:
        print(f"Destination Container: {dest_container} (DB: {dest_db_name})")
    print("-" * 60)

    # 1. Connect to local source MongoDB
    try:
        source_client = MongoClient(source_uri, serverSelectionTimeoutMS=5000)
        source_client.admin.command("ping")
        source_db = source_client[source_db_name]
        col_name = os.getenv("FACE_AUTH_APP_SETTINGS_COLLECTION", "app_settings")
        source_col = source_db[col_name]
    except Exception as exc:
        print(f"❌ Error connecting to source MongoDB at {source_uri}: {exc}")
        sys.exit(1)

    # 2. Query ONLY the email templates document
    template_doc = source_col.find_one({"doc_type": "email_templates"})
    if not template_doc:
        print(f"❌ No email templates document (doc_type='email_templates') found in source collection '{col_name}'.")
        source_client.close()
        sys.exit(1)

    templates_list = template_doc.get("email_templates", [])
    print(f"✅ Found email templates in local MongoDB:")
    print(f"   • Template Count: {len(templates_list)}")
    for idx, t in enumerate(templates_list, start=1):
        key = t.get("template_key", "unknown")
        name = t.get("name", "Untitled")
        print(f"     [{idx}] Key: '{key}' | Name: '{name}'")

    updated_at = template_doc.get("updated_at")
    print(f"   • Source Updated At: {updated_at}")

    if dry_run:
        print("\n🔍 DRY-RUN complete. No changes made to destination MongoDB.")
        source_client.close()
        return

    # 3. Migrate to Destination
    print("\nStarting migration into destination MongoDB...")

    if not updated_at:
        template_doc["updated_at"] = datetime.now(timezone.utc)

    # Convert to standard Extended JSON for import
    json_doc = json_util.dumps(template_doc)

    if dest_uri:
        # Direct PyMongo connection
        try:
            dest_client = MongoClient(dest_uri, serverSelectionTimeoutMS=5000)
            dest_db = dest_client[dest_db_name]
            dest_col = dest_db[col_name]
            dest_col.replace_one({"doc_type": "email_templates"}, template_doc, upsert=True)
            dest_client.close()
            print("✅ Successfully upserted email templates via PyMongo direct connection!")
        except Exception as exc:
            print(f"❌ Failed to write to destination via PyMongo: {exc}")
            source_client.close()
            sys.exit(1)
    else:
        # Import directly into running Docker container via mongoimport
        try:
            # Check if container is running
            check_cmd = subprocess.run(
                ["docker", "inspect", "-f", "{{.State.Running}}", dest_container],
                capture_output=True,
                text=True,
                check=False,
            )
            if check_cmd.returncode != 0 or check_cmd.stdout.strip() != "true":
                print(f"❌ Docker container '{dest_container}' is not running.")
                print("   Please start your docker containers with: docker compose up -d")
                source_client.close()
                sys.exit(1)

            import_proc = subprocess.run(
                [
                    "docker",
                    "exec",
                    "-i",
                    dest_container,
                    "mongoimport",
                    "--db",
                    dest_db_name,
                    "--collection",
                    col_name,
                    "--mode",
                    "upsert",
                    "--upsertFields",
                    "doc_type",
                ],
                input=json_doc,
                capture_output=True,
                text=True,
                check=False,
            )

            if import_proc.returncode != 0:
                print(f"❌ Failed to import into container '{dest_container}':")
                print(import_proc.stderr)
                source_client.close()
                sys.exit(1)

            print(f"✅ Successfully imported into container '{dest_container}'.")

        except Exception as exc:
            print(f"❌ Docker execution error: {exc}")
            source_client.close()
            sys.exit(1)

    source_client.close()

    # 4. Verification
    print("\nVerifying migrated data in Docker MongoDB...")
    verify_proc = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            dest_container,
            "mongosh",
            dest_db_name,
            "--quiet",
            "--eval",
            f"const d = db.{col_name}.findOne({{doc_type: 'email_templates'}}); print(JSON.stringify({{count: d ? d.email_templates.length : 0, keys: d ? d.email_templates.map(t => t.template_key) : []}}));",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if verify_proc.returncode == 0 and "count" in verify_proc.stdout:
        print(f"✅ Verification successful! Destination details:")
        print(f"   {verify_proc.stdout.strip()}")
        print("\n🎉 Email templates migrated successfully! The application will now display your email templates.")
    else:
        print(f"⚠️ Verification check returned: {verify_proc.stderr or verify_proc.stdout}")


def main():
    parser = argparse.ArgumentParser(description="Migrate email templates from local MongoDB to Docker MongoDB")
    parser.add_argument(
        "--source-uri",
        default=os.getenv("SOURCE_MONGO_URI", "mongodb://localhost:27017"),
        help="Local/Source MongoDB URI",
    )
    parser.add_argument(
        "--source-db",
        default=os.getenv("SOURCE_MONGO_DB", "predator"),
        help="Source database name",
    )
    parser.add_argument(
        "--container",
        default=os.getenv("DOCKER_CONTAINER", "predator-mongo"),
        help="Target Docker container name",
    )
    parser.add_argument(
        "--dest-db",
        default=os.getenv("DEST_MONGO_DB", "predator"),
        help="Destination database name",
    )
    parser.add_argument(
        "--dest-uri",
        default=os.getenv("DEST_MONGO_URI", None),
        help="Destination Mongo URI (optional, if port exposed)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show templates to be migrated without modifying destination",
    )

    args = parser.parse_args()

    migrate_templates(
        source_uri=args.source_uri,
        source_db_name=args.source_db,
        dest_container=args.container,
        dest_db_name=args.dest_db,
        dest_uri=args.dest_uri,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
