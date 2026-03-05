# -*- coding: utf-8 -*-
import os
import hashlib
import zipfile
import re

PAGES_URL = "https://addonniss.github.io/repository.addonniss"

SERVICE_ID = "service.translatarr"
REPO_ID = "repository.addonniss"


def get_version(xml_path):
    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'version=["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', content)
        if match:
            return match.group(1)
    raise ValueError(f"Invalid version in {xml_path}")


def clean_generated():
    """
    Remove ONLY generated files.
    Never delete actual addon source folders.
    """

    # Remove old repository zip
    for f in os.listdir("."):
        if f.startswith("repository.addonniss-") and f.endswith(".zip"):
            os.remove(f)

    # Remove generated metadata
    if os.path.exists("addons.xml"):
        os.remove("addons.xml")

    if os.path.exists("addons.xml.md5"):
        os.remove("addons.xml.md5")

    # Remove old service zip (but NOT the folder itself)
    if os.path.exists(SERVICE_ID):
        for f in os.listdir(SERVICE_ID):
            if f.endswith(".zip"):
                os.remove(os.path.join(SERVICE_ID, f))


def build_service_zip():
    """
    Build service.translatarr zip inside its folder.
    """

    service_xml_path = os.path.join(SERVICE_ID, "addon.xml")

    if not os.path.exists(service_xml_path):
        raise FileNotFoundError(
            f"{service_xml_path} not found. Make sure the addon folder exists."
        )

    version = get_version(service_xml_path)
    zip_name = f"{SERVICE_ID}-{version}.zip"
    zip_path = os.path.join(SERVICE_ID, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(SERVICE_ID):
            for file in files:
                full_path = os.path.join(root, file)

                # Do not include the zip inside itself
                if full_path.endswith(".zip"):
                    continue

                arcname = os.path.join(
                    SERVICE_ID,
                    os.path.relpath(full_path, SERVICE_ID)
                )
                z.write(full_path, arcname)

    return service_xml_path


def build_repository_zip():
    """
    Build repository.addonniss zip at ROOT.
    """

    repo_xml_path = "addon.xml"

    if not os.path.exists(repo_xml_path):
        raise FileNotFoundError("Root addon.xml not found.")

    version = get_version(repo_xml_path)
    zip_name = f"{REPO_ID}-{version}.zip"

    with open(repo_xml_path, "r", encoding="utf-8") as f:
        repo_xml = f.read()

    # Replace raw GitHub links with Pages root URL
    repo_xml = repo_xml.replace(
        "https://raw.githubusercontent.com/Addonniss/repository.addonniss/main/",
        f"{PAGES_URL}/"
    )

    temp_xml = "temp_repo_addon.xml"
    with open(temp_xml, "w", encoding="utf-8", newline="\n") as f:
        f.write(repo_xml)

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(temp_xml, os.path.join(REPO_ID, "addon.xml"))

        if os.path.exists("icon.png"):
            z.write("icon.png", os.path.join(REPO_ID, "icon.png"))

    os.remove(temp_xml)

    return repo_xml_path


def generate_addons_xml(xml_files):
    """
    Generate root addons.xml and addons.xml.md5
    """

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
    clean_generated()
    service_xml = build_service_zip()
    repo_xml = build_repository_zip()
    generate_addons_xml([service_xml, repo_xml])
    print("Repository build complete.")
