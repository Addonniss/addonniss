import os
import hashlib
import zipfile

# This script creates the zips/ folder, the addons.xml, and the .md5
def create_repo():
    addons = ['service.translatarr', 'repository.addonniss'] # Add more here later
    zips_path = 'zips'
    
    if not os.path.exists(zips_path):
        os.makedirs(zips_path)

    xml_content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    for addon in addons:
        # 1. Find the addon.xml for each project
        xml_path = os.path.join(addon, 'addon.xml')
        if os.path.exists(xml_path):
            with open(xml_path, 'r', encoding='utf-8') as f:
                # Strip the header and append to master XML
                lines = f.readlines()
                xml_content += "".join(lines[1:]) + "\n"
    
    xml_content += u'</addons>\n'

    # 2. Write the master addons.xml
    with open(os.path.join(zips_path, 'addons.xml'), 'w', encoding='utf-8') as f:
        f.write(xml_content)

    # 3. Create the MD5
    md5_hash = hashlib.md5(xml_content.encode('utf-8')).hexdigest()
    with open(os.path.join(zips_path, 'addons.xml.md5'), 'w') as f:
        f.write(md5_hash)

    print("Success: Updated addons.xml and MD5!")

if __name__ == "__main__":
    create_repo()
