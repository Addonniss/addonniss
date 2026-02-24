import os
import hashlib
import zipfile
import shutil
import re

def get_version(xml_path):
    """Extract version string from addon.xml reliably."""
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'version=["\']([^"\']+)["\']', content)
            if match:
                return match.group(1).strip()
    except Exception as e:
        print(f"Error reading version from {xml_path}: {e}")
    raise ValueError(f"Cannot find version in {xml_path}")  # force error if missing

def create_repo():
    service_id = 'service.translatarr'
    repo_id = 'repository.addonniss'
    zips_path = 'zips'

    # Clear previous zips
    if os.path.exists(zips_path):
        shutil.rmtree(zips_path)
    os.makedirs(zips_path)

    xml_content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    for addon_id in [service_id, repo_id]:
        addon_dir = addon_id if addon_id == service_id else "."
        xml_path = os.path.join(addon_dir, 'addon.xml')

        if not os.path.exists(xml_path):
            print(f"Warning: {xml_path} not found, skipping {addon_id}")
            continue

        v = get_version(xml_path)
        print(f"Found version {v} for {addon_id}")

        # Read the addon.xml content (skip XML declaration)
        with open(xml_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            xml_content += "".join(lines[1:]).strip() + "\n"

        # Create target ZIP
        target_dir = os.path.join(zips_path, addon_id)
        os.makedirs(target_dir, exist_ok=True)
        zip_name = f"{addon_id}-{v}.zip"
        zip_path = os.path.join(target_dir, zip_name)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            if addon_id == service_id:
                # Add all files from service.translatarr
                for root, _, files in os.walk(service_id):
                    for file in files:
                        fp = os.path.join(root, file)
                        arcname = os.path.join(service_id, os.path.relpath(fp, service_id))
                        z.write(fp, arcname)
            else:
                # Repository zip
                z.write('addon.xml', os.path.join(repo_id, 'addon.xml'))
                if os.path.exists('icon.png'):
                    z.write('icon.png', os.path.join(repo_id, 'icon.png'))

    xml_content += '</addons>\n'

    # Save addons.xml with consistent line endings
    addons_xml_path = os.path.join(zips_path, 'addons.xml')
    with open(addons_xml_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(xml_content)

    # Compute and save MD5
    md5 = hashlib.md5(xml_content.encode('utf-8')).hexdigest()
    with open(os.path.join(zips_path, 'addons.xml.md5'), 'w', encoding='utf-8') as f:
        f.write(md5.strip())

    print("Repository generation complete.")

if __name__ == "__main__":
    create_repo()
