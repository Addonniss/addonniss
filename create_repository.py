import os
import hashlib
import zipfile
import shutil
import re

def get_version(xml_path):
    try:
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'version="([^"]+)"', content)
            return match.group(1) if match else "1.0.0"
    except:
        return "1.0.0"

def create_repo():
    service_id = 'service.translatarr'
    repo_id = 'repository.addonniss'
    zips_path = 'zips'
    
    # 1. COMPLETELY WIPE THE ZIPS FOLDER
    if os.path.exists(zips_path):
        shutil.rmtree(zips_path)
    os.makedirs(zips_path)

    xml_content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    # 2. PROCESS FOLDERS
    for addon_id in [service_id, repo_id]:
        addon_dir = addon_id if addon_id == service_id else "."
        xml_path = os.path.join(addon_dir, 'addon.xml')
        
        if not os.path.exists(xml_path):
            continue

        version = get_version(xml_path)
        print(f"Detected {addon_id} version: {version}")

        # Add to master XML
        with open(xml_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            xml_content += "".join(lines[1:]) + "\n"

        # Create Zip subfolder
        target_dir = os.path.join(zips_path, addon_id)
        os.makedirs(target_dir)
        
        zip_name = f"{addon_id}-{version}.zip"
        with zipfile.ZipFile(os.path.join(target_dir, zip_name), 'w', zipfile.ZIP_DEFLATED) as z:
            if addon_id == service_id:
                for root, _, files in os.walk(service_id):
                    for file in files:
                        fp = os.path.join(root, file)
                        z.write(fp, os.path.join(service_id, os.path.relpath(fp, service_id)))
            else:
                z.write('addon.xml', os.path.join(repo_id, 'addon.xml'))
                for extra in ['icon.png', 'fanart.jpg']:
                    if os.path.exists(extra):
                        z.write(extra, os.path.join(repo_id, extra))

    # 3. FINALIZE
    xml_content += u'</addons>\n'
    with open(os.path.join(zips_path, 'addons.xml'), 'w', encoding='utf-8') as f:
        f.write(xml_content)
    md5 = hashlib.md5(xml_content.encode('utf-8')).hexdigest()
    with open(os.path.join(zips_path, 'addons.xml.md5'), 'w') as f:
        f.write(md5)

if __name__ == "__main__":
    create_repo()
