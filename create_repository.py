import os
import hashlib
import zipfile
import shutil

def create_repo():
    service_id = 'service.translatarr'
    repo_id = 'repository.addonniss'
    zips_path = 'zips'
    
    if os.path.exists(zips_path):
        shutil.rmtree(zips_path)
    os.makedirs(zips_path)

    xml_content = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<addons>\n'

    # --- PART A: ZIP THE SERVICE ---
    if os.path.exists(service_id):
        xml_path = os.path.join(service_id, 'addon.xml')
        with open(xml_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            version = next((line.split('version="')[1].split('"')[0] for line in lines if 'version="' in line), "1.0.0")
            xml_content += "".join(lines[1:]) + "\n"

        target_dir = os.path.join(zips_path, service_id)
        os.makedirs(target_dir)
        zip_name = f"{service_id}-{version}.zip"
        with zipfile.ZipFile(os.path.join(target_dir, zip_name), 'w', zipfile.ZIP_DEFLATED) as z:
            for root, _, files in os.walk(service_id):
                for file in files:
                    fp = os.path.join(root, file)
                    # Correct structure: folder_name/file
                    z.write(fp, os.path.join(service_id, os.path.relpath(fp, service_id)))

    # --- PART B: ZIP THE REPOSITORY ---
    repo_xml = 'addon.xml'
    if os.path.exists(repo_xml):
        with open(repo_xml, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            repo_version = next((line.split('version="')[1].split('"')[0] for line in lines if 'version="' in line), "1.0.0")
            xml_content += "".join(lines[1:]) + "\n"

        target_dir = os.path.join(zips_path, repo_id)
        os.makedirs(target_dir)
        zip_name = f"{repo_id}-{repo_version}.zip"
        with zipfile.ZipFile(os.path.join(target_dir, zip_name), 'w', zipfile.ZIP_DEFLATED) as z:
            # IMPORTANT: Put files inside a folder named repository.addonniss inside the zip
            z.write(repo_xml, os.path.join(repo_id, repo_xml))
            for extra in ['icon.png', 'fanart.jpg']:
                if os.path.exists(extra):
                    z.write(extra, os.path.join(repo_id, extra))

    # --- PART C: FINALIZE ---
    xml_content += u'</addons>\n'
    with open(os.path.join(zips_path, 'addons.xml'), 'w', encoding='utf-8') as f:
        f.write(xml_content)
    md5_hash = hashlib.md5(xml_content.encode('utf-8')).hexdigest()
    with open(os.path.join(zips_path, 'addons.xml.md5'), 'w') as f:
        f.write(md5_hash)

if __name__ == "__main__":
    create_repo()
