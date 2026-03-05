# -*- coding: utf-8 -*-
import os
import hashlib
import zipfile
import shutil
import re
import sys

PAGES_URL = "https://addonniss.github.io/repository.addonniss"

SERVICE_ID = "service.translatarr"
REPO_ID = "repository.addonniss"

# Absolute paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_PATH = os.path.join(SCRIPT_DIR, SERVICE_ID)


def get_version(xml_path):
    xml_path = os.path.abspath(xml_path)
    if not os.path.exists(xml_path):
        print(f"[ERROR] Version file not found: {xml_path}")
        sys.exit(1)
    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'version=["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', content)
        if match:
            return match.group(1)
    raise ValueError(f"Invalid version in {xml_path}")


def clean():
    print("[INFO] Cleaning old generated files...")
    for f in os.listdir(SCRIPT_DIR):
        f_path = os.path.join(SCRIPT_DIR, f)
        if f.startswith(REPO_ID + "-") and f.endswith(".zip"):
            os.remove(f_path)
        if f in ["addons.xml", "addons.xml.md5"]:
            os.remove(f_path)

    if os.path.exists(SERVICE_PATH):
        shutil.rmtree(os.path.join(SCRIPT_DIR, SERVICE_ID + "_tmp"), ignore_errors=True)


def build_service():
    if not os.path.exists(SERVICE_PATH):
        print(f"[ERROR] Service folder missing: {SERVICE_PATH}")
        sys.exit(1)

    print(f"[INFO] Service folder contents: {os.listdir(SERVICE_PATH)}")
    version = get_version(os.path.join(SERVICE_PATH, "addon.xml"))
    zip_name = f"{SERVICE_ID}-{version}.zip"
    zip_path = os.path.join(SCRIPT_DIR, SERVICE_ID, zip_name)

    os.makedirs(os.path.join(SCRIPT_DIR, SERVICE_ID), exist_ok=True)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(SERVICE_PATH):
            for file in files:
                fp = os.path.join(root, file)
                arcname = os.path.join(SERVICE_ID, os.path.relpath(fp, SERVICE_PATH))
                z.write(fp, arcname)

    print(f"[INFO] Built service zip: {zip_path}")
    return os.path.join(SERVICE_PATH, "addon.xml")


def build_repo():
    repo_xml_path = os.path.join(SCRIPT_DIR, "addon.xml")
    version = get_version(repo_xml_path)
    zip_name = f"{REPO_ID}-{version}.zip"

    with open(repo_xml_path, "r", encoding="utf-8") as f:
        repo_xml = f.read()

    repo_xml = repo_xml.replace(
        "https://raw.githubusercontent.com/Addonniss/repository.addonniss/main/",
        f"{PAGES_URL}/"
    )

    temp_xml = os.path.join(SCRIPT_DIR, "temp_repo.xml")
    with open(temp_xml, "w", encoding="utf-8", newline="\n") as f:
        f.write(repo_xml)

    with zipfile.ZipFile(os.path.join(SCRIPT_DIR, zip_name), "w", zipfile.ZIP_DEFLATED) as z:
        z.write(temp_xml, os.path.join(REPO_ID, "addon.xml"))
        icon_path = os.path.join(SCRIPT_DIR, "icon.png")
        if os.path.exists(icon_path):
            z.write(icon_path, os.path.join(REPO_ID, "icon.png"))

    os.remove(temp_xml)
    print(f"[INFO] Built repository zip: {zip_name}")
    return repo_xml_path


def generate_addons_xml(xml_files):
    print("[INFO] Generating addons.xml and addons.xml.md5...")
    content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    for xml_path in xml_files:
        with open(xml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            content += "".join(lines[1:]).strip() + "\n"
    content += "</addons>\n"

    addons_xml_path = os.path.join(SCRIPT_DIR, "addons.xml")
    with open(addons_xml_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content.strip() + "\n")

    md5 = hashlib.md5(content.encode("utf-8")).hexdigest()
    with open(os.path.join(SCRIPT_DIR, "addons.xml.md5"), "w", encoding="utf-8") as f:
        f.write(md5)
    print("[INFO] addons.xml and MD5 generated.")


if __name__ == "__main__":
    print("[INFO] Script running in:", SCRIPT_DIR)
    if not os.path.exists(SERVICE_PATH):
        print(f"[ERROR] Missing folder: {SERVICE_PATH}")
        sys.exit(1)
    print("[INFO] Found service.translatarr folder:", os.listdir(SERVICE_PATH))

    clean()
    service_xml = build_service()
    repo_xml = build_repo()
    generate_addons_xml([service_xml, repo_xml])
    print("[SUCCESS] Repository build complete.")
