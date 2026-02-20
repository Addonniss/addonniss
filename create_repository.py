import os
import hashlib
import zipfile
import shutil

def create_repo():
    service_id = 'service.translatarr'
    repo_id = 'repository.addonniss'
    # FORCE THE VERSION STRING - NO CALCULATION
    VERSION = "1.0.0" 
    
    zips_path = 'zips'
    if os.path.exists(zips_path):
        shutil.rmtree(zips_path)
    os.makedirs(zips_path)

    xml_content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    for addon_id in [service_id, repo_id]:
        addon_dir = addon_id if addon_id == service_id else "."
        xml_path = os.path.join(addon_dir, 'addon.xml')
        
        if not os.path.exists(xml_path):
            continue

        # Add to master XML
        with open(xml_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            xml_content += "".join(lines[1:]) + "\n"

        target_dir = os.path.join(zips_path, addon_id)
        os.makedirs(target_dir)
        
        # USE THE FORCED VERSION STRING
        zip_name = f"{addon_id}-{VERSION}.zip"
        zip_path = os.path.join(target_dir, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            if addon_id == service_id:
                for root, _, files in os.walk(service_id):
                    for file in files:
                        fp = os.path.join(root, file)
                        z.write(fp, os.path.join(service_id, os.path.relpath(fp, service_id)))
            else:
                z.write('addon.xml', os.path.join(repo_id, 'addon.xml'))
                if os.path.exists('icon.png'):
                    z.write('icon.png', os.path.join(repo_id, 'icon.png'))
        print(f"Successfully created {zip_name}")

    # Finalize
    xml_content += u'</addons>\n'
    with open(os.path.join(zips_path, 'addons.xml'), 'w', encoding='utf-8') as f:
        f.write(xml_content)
    md5 = hashlib.md5(xml_content.encode('utf-8')).hexdigest()
    with open(os.path.join(zips_path, 'addons.xml.md5'), 'w') as f:
        f.write(md5)

if __name__ == "__main__":
    create_repo()
