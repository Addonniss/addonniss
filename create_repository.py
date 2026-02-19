import os
import hashlib
import zipfile
import shutil

def create_repo():
    service_id = 'service.translatarr'
    repo_id = 'repository.addonniss'
    version = '1.0.0'  # <--- FORCED VERSION
    zips_path = 'zips'
    
    # Start fresh
    if os.path.exists(zips_path):
        shutil.rmtree(zips_path)
    os.makedirs(zips_path)

    xml_content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    # 1. Process Service
    if os.path.exists(service_id):
        with open(os.path.join(service_id, 'addon.xml'), 'r', encoding='utf-8') as f:
            xml_content += "".join(f.readlines()[1:]) + "\n"
        
        s_dir = os.path.join(zips_path, service_id)
        os.makedirs(s_dir)
        with zipfile.ZipFile(os.path.join(s_dir, f"{service_id}-{version}.zip"), 'w', zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(service_id):
                for file in files:
                    fp = os.path.join(root, file)
                    z.write(fp, os.path.join(service_id, os.path.relpath(fp, service_id)))

    # 2. Process Repository
    with open('addon.xml', 'r', encoding='utf-8') as f:
        xml_content += "".join(f.readlines()[1:]) + "\n"
    
    r_dir = os.path.join(zips_path, repo_id)
    os.makedirs(r_dir)
    with zipfile.ZipFile(os.path.join(r_dir, f"{repo_id}-{version}.zip"), 'w', zipfile.ZIP_DEFLATED) as z:
        z.write('addon.xml', os.path.join(repo_id, 'addon.xml'))
        for extra in ['icon.png', 'fanart.jpg']:
            if os.path.exists(extra):
                z.write(extra, os.path.join(repo_id, extra))

    # 3. Finalize Index
    xml_content += u'</addons>\n'
    with open(os.path.join(zips_path, 'addons.xml'), 'w', encoding='utf-8') as f:
        f.write(xml_content)
    
    md5 = hashlib.md5(xml_content.encode('utf-8')).hexdigest()
    with open(os.path.join(zips_path, 'addons.xml.md5'), 'w') as f:
        f.write(md5)

if __name__ == "__main__":
    create_repo()
