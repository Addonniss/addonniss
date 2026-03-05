import os
import hashlib
import zipfile
import shutil
import re

# GitHub Pages base URL
PAGES_URL = "https://addonniss.github.io/repository.addonniss/zips"

def get_version(xml_path):
    """Extract the version string exactly in x.x.x format from addon.xml"""
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'version=["\']([0-9]+\.[0-9]+\.[0-9]+)["\']', content)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Error reading version from {xml_path}: {e}")
    raise ValueError(f"Cannot find proper x.x.x version in {xml_path}")

def create_repo():
    service_id = 'service.translatarr'
    repo_id = 'repository.addonniss'
    zips_path = 'zips'

    # Remove old zips folder
    if os.path.exists(zips_path):
        shutil.rmtree(zips_path)
    os.makedirs(zips_path)

    # Start addons.xml content
    xml_content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    for addon_id in [service_id, repo_id]:
        addon_dir = addon_id if addon_id == service_id else "."
        xml_path = os.path.join(addon_dir, 'addon.xml')

        if not os.path.exists(xml_path):
            print(f"Warning: {xml_path} not found, skipping {addon_id}")
            continue

        # Get exact x.x.x version
        v = get_version(xml_path)
        print(f"Found version {v} for {addon_id}")

        # Read addon.xml, skip XML declaration
        with open(xml_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            xml_content += "".join(lines[1:]).strip() + "\n"

        # Create ZIP
        target_dir = os.path.join(zips_path, addon_id)
        os.makedirs(target_dir, exist_ok=True)
        zip_name = f"{addon_id}-{v}.zip"
        zip_path = os.path.join(target_dir, zip_name)

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            if addon_id == service_id:
                # Include all files in service addon
                for root, _, files in os.walk(service_id):
                    for file in files:
                        fp = os.path.join(root, file)
                        arcname = os.path.join(service_id, os.path.relpath(fp, service_id))
                        z.write(fp, arcname)
            else:
                # Repository zip
                # Automatically update URLs to GitHub Pages inside addon.xml
                with open('addon.xml', 'r', encoding='utf-8') as f:
                    repo_xml = f.read()
                repo_xml = repo_xml.replace(
                    'https://raw.githubusercontent.com/Addonniss/repository.addonniss/main/zips/addons.xml',
                    f'{PAGES_URL}/addons.xml'
                ).replace(
                    'https://raw.githubusercontent.com/Addonniss/repository.addonniss/main/zips/addons.xml.md5',
                    f'{PAGES_URL}/addons.xml.md5'
                ).replace(
                    'https://raw.githubusercontent.com/Addonniss/repository.addonniss/main/zips/',
                    f'{PAGES_URL}/'
                )
                temp_path = os.path.join(target_dir, 'addon.xml')
                with open(temp_path, 'w', encoding='utf-8', newline='\n') as f:
                    f.write(repo_xml)
                z.write(temp_path, os.path.join(repo_id, 'addon.xml'))
                if os.path.exists('icon.png'):
                    z.write('icon.png', os.path.join(repo_id, 'icon.png'))

    xml_content += '</addons>\n'

    # Write addons.xml
    addons_xml_path = os.path.join(zips_path, 'addons.xml')
    with open(addons_xml_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(xml_content)

    # Write addons.xml.md5
    md5 = hashlib.md5(xml_content.encode('utf-8')).hexdigest()
    with open(os.path.join(zips_path, 'addons.xml.md5'), 'w', encoding='utf-8') as f:
        f.write(md5.strip())

    print("Repository generation complete.")

if __name__ == "__main__":
    create_repo()
