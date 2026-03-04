import os
import hashlib
import zipfile
import shutil
import re

# -----------------------------
# Configuration
# -----------------------------
PAGES_URL = "https://addonniss.github.io/repository.addonniss/zips"
SERVICE_ID = "service.translatarr"
REPO_ID = "repository.addonniss"
ZIPS_PATH = "zips"

# -----------------------------
# Helpers
# -----------------------------
def get_version(xml_path):
    """Extract version in x.x.x format from addon.xml"""
    with open(xml_path, 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'version=["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', content)
        if match:
            return match.group(1)
    raise ValueError(f"Invalid version format in {xml_path}")

def clean_zips():
    if os.path.exists(ZIPS_PATH):
        shutil.rmtree(ZIPS_PATH)
    os.makedirs(ZIPS_PATH)

# -----------------------------
# Build Service Addon ZIP
# -----------------------------
def build_service():
    xml_path = os.path.join(SERVICE_ID, "addon.xml")
    version = get_version(xml_path)

    target_folder = os.path.join(ZIPS_PATH, SERVICE_ID)
    os.makedirs(target_folder, exist_ok=True)

    zip_name = f"{SERVICE_ID}-{version}.zip"
    zip_path = os.path.join(target_folder, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(SERVICE_ID):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.join(SERVICE_ID, os.path.relpath(full_path, SERVICE_ID))
                z.write(full_path, arcname)

    return xml_path

# -----------------------------
# Build Repository Addon ZIP
# -----------------------------
def build_repo():
    xml_path = "addon.xml"
    version = get_version(xml_path)

    zip_name = f"{REPO_ID}-{version}.zip"
    zip_path = os.path.join(ZIPS_PATH, zip_name)

    with open(xml_path, "r", encoding="utf-8") as f:
        repo_xml = f.read()

    # Replace URLs for GitHub Pages
    repo_xml = repo_xml.replace(
        "https://raw.githubusercontent.com/Addonniss/repository.addonniss/main/zips/",
        f"{PAGES_URL}/"
    )

    temp_xml = os.path.join(ZIPS_PATH, "repo_addon.xml")
    with open(temp_xml, "w", encoding="utf-8", newline="\n") as f:
        f.write(repo_xml)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(temp_xml, os.path.join(REPO_ID, "addon.xml"))
        if os.path.exists("icon.png"):
            z.write("icon.png", os.path.join(REPO_ID, "icon.png"))

    os.remove(temp_xml)
    return xml_path

# -----------------------------
# Generate addons.xml & MD5
# -----------------------------
def generate_addons_xml(xml_files):
    content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'
    for xml_path in xml_files:
        with open(xml_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            content += "".join(lines[1:]).strip() + "\n"
    content += "</addons>\n"
    final_xml = content.strip() + "\n"

    # Write addons.xml
    with open(os.path.join(ZIPS_PATH, "addons.xml"), "w", encoding="utf-8", newline="\n") as f:
        f.write(final_xml)

    # Write MD5
    md5_hash = hashlib.md5(final_xml.encode("utf-8")).hexdigest()
    with open(os.path.join(ZIPS_PATH, "addons.xml.md5"), "w", encoding="utf-8", newline="\n") as f:
        f.write(md5_hash)

# -----------------------------
# Main Execution
# -----------------------------
if __name__ == "__main__":
    clean_zips()
    service_xml = build_service()
    repo_xml = build_repo()
    generate_addons_xml([service_xml, repo_xml])
    print("Repository build complete.")
