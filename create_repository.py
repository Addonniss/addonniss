import os
import hashlib
import zipfile
import shutil

def create_repo():
    # 1. Configuration
    addons = ['service.translatarr', 'repository.addonniss']
    zips_path = 'zips'
    
    if os.path.exists(zips_path):
        shutil.rmtree(zips_path) # Clean start
    os.makedirs(zips_path)

    xml_content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    for addon in addons:
        if not os.path.exists(addon):
            print(f"Skipping {addon}: Folder not found")
            continue

        # 2. Parse the addon.xml to get the version
        xml_path = os.path.join(addon, 'addon.xml')
        with open(xml_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Extract version string
            version = ""
            for line in lines:
                if 'version="' in line:
                    version = line.split('version="')[1].split('"')[0]
                    break
            xml_content += "".join(lines[1:]) + "\n"

        # 3. Create the addon's zip folder
        addon_zip_dir = os.path.join(zips_path, addon)
        os.makedirs(addon_zip_dir)
        
        # 4. ZIP the addon folder
        zip_name = f"{addon}-{version}.zip"
        zip_path = os.path.join(addon_zip_dir, zip_name)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
            for root, dirs, files in os.walk(addon):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Correct path inside the zip
                    arcname = os.path.join(addon, os.path.relpath(file_path, addon))
                    z.write(file_path, arcname)
        
        print(f"Created: {zip_path}")

    xml_content += u'</addons>\n'

    # 5. Save the master XML and MD5
    with open(os.path.join(zips_path, 'addons.xml'), 'w', encoding='utf-8') as f:
        f.write(xml_content)

    md5_hash = hashlib.md5(xml_content.encode('utf-8')).hexdigest()
    with open(os.path.join(zips_path, 'addons.xml.md5'), 'w') as f:
        f.write(md5_hash)

if __name__ == "__main__":
    create_repo()
