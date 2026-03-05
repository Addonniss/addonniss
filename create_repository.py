# -*- coding: utf-8 -*-
import os
import hashlib
import zipfile
import shutil
import re
import os

print("Current folder:", os.getcwd())
print("List files in root:", os.listdir("."))
print("service.translatarr exists?", os.path.exists("service.translatarr"))

PAGES_URL = "https://addonniss.github.io/repository.addonniss"

SERVICE_ID = "service.translatarr"
REPO_ID = "repository.addonniss"
ZIPS_DIR = "zips"


def get_version(xml_path):
    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'version=["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', content)
        if match:
            return match.group(1)
    raise ValueError(f"Invalid version in {xml_path}")


def clean():
    # remove old generated files
    if os.path.exists(ZIPS_DIR):
        shutil.rmtree(ZIPS_DIR)
    if os.path.exists("addons.xml"):
        os.remove("addons.xml")
    if os.path.exists("addons.xml.md5"):
        os.remove("addons.xml.md5")
    if os.path.exists(SERVICE_ID):
        shutil.rmtree(SERVICE_ID)


def build_service():
    version = get_version(os.path.join(SERVICE_ID, "addon.xml"))
    zip_name = f"{SERVICE_ID}-{version}.zip"

    os.makedirs(SERVICE_ID, exist_ok=True)
    os.makedirs(ZIPS_DIR, exist_ok=True)

    zip_path = os.path.join(ZIPS_DIR, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(SERVICE_ID):
            for file in files:
                fp = os.path.join(root, file)
                arcname = os.path.join(SERVICE_ID, os.path.relpath(fp, SERVICE_ID))
                z.write(fp, arcname)

    return os.path.join(SERVICE_ID, "addon.xml")


def build_repo():
    version = get_version("addon.xml")
    zip_name = f"{REPO_ID}-{version}.zip"

    os.makedirs(ZIPS_DIR, exist_ok=True)

    with open("addon.xml", "r", encoding="utf-8") as f:
        repo_xml = f.read()

    repo_xml = repo_xml.replace(
        "https://raw.githubusercontent.com/Addonniss/repository.addonniss/main/",
        f"{PAGES_URL}/"
    )

    temp_xml = "temp_repo.xml"
    with open(temp_xml, "w", encoding="utf-8", newline="\n") as f:
        f.write(repo_xml)

    with zipfile.ZipFile(os.path.join(ZIPS_DIR, zip_name), "w", zipfile.ZIP_DEFLATED) as z:
        z.write(temp_xml, os.path.join(REPO_ID, "addon.xml"))
        if os.path.exists("icon.png"):
            z.write("icon.png", os.path.join(REPO_ID, "icon.png"))

    os.remove(temp_xml)

    return "addon.xml"


def generate_addons_xml(xml_files):
    content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    for xml_path in xml_files:
        with open(xml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            content += "".join(lines[1:]).strip() + "\n"
    content += "</addons>\n"

    with open("addons.xml", "w", encoding="utf-8", newline="\n") as f:
        f.write(content.strip() + "\n")

    md5 = hashlib.md5(content.encode("utf-8")).hexdigest()
    with open("addons.xml.md5", "w", encoding="utf-8") as f:
        f.write(md5)


if __name__ == "__main__":
    clean()
    service_xml = build_service()
    repo_xml = build_repo()
    generate_addons_xml([service_xml, repo_xml])
    print("Repository build complete.")
