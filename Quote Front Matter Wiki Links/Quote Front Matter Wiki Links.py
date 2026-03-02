import os
import re

# ================= CONFIGURATION =================
IS_DRY_RUN = False  # STAYS TRUE: No files will be modified on disk.
VAULT_PATH = '/Volumes/ObsidianSync/My Vault'
# =================================================

# Regex 1: Find unquoted WikiLinks (key: [[Link]])
QUOTE_PATTERN = r'^([\w\-_]+:\s*)(?!(?:"|\'))(\[\[.*?\]\])$'

# Regex 2: Find WikiLinks with paths inside quotes (key: "[[path/to/File]]")
PATH_STRIP_PATTERN = r'^([\w\-_]+:\s*)"\[\[(?:.*/)?(.*?)\]\]"'

def process_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return None, [{'key': 'Error', 'msg': str(e)}]

    parts = content.split('---', 2)
    if len(parts) < 3 or not content.startswith('---'):
        return None 

    front_matter = parts[1]
    original_fm = front_matter
    changes = []

    # --- STEP 1: Quote unquoted links ---
    unquoted_matches = re.findall(QUOTE_PATTERN, front_matter, flags=re.MULTILINE)
    for key_part, link in unquoted_matches:
        key = key_part.replace(':', '').strip()
        changes.append({'key': key, 'msg': f"Quoted: {link} -> \"{link}\""})
    
    front_matter = re.sub(QUOTE_PATTERN, r'\1"\2"', front_matter, flags=re.MULTILINE)

    # --- STEP 2: Strip paths from WikiLinks ---
    path_matches = re.findall(PATH_STRIP_PATTERN, front_matter, flags=re.MULTILINE)
    for key_part, filename in path_matches:
        path_check = fr'^{re.escape(key_part)}"\[\[(.*?/){re.escape(filename)}\]\]"'
        if re.search(path_check, front_matter, flags=re.MULTILINE):
            key = key_part.replace(':', '').strip()
            changes.append({'key': key, 'msg': f"Stripped Path: [[.../{filename}]] -> [[{filename}]]"})
    
    front_matter = re.sub(PATH_STRIP_PATTERN, r'\1"[[\2]]"', front_matter, flags=re.MULTILINE)

    if front_matter == original_fm:
        return None

    new_full_content = '---'.join(['', front_matter, parts[2]])
    return new_full_content, changes

def run_vault_update():
    if not os.path.exists(VAULT_PATH):
        print(f"❌ Path not found: {VAULT_PATH}")
        return

    print(f"\n{'='*75}\nMODE: {'🔍 DRY RUN (Read-Only)' if IS_DRY_RUN else '🚀 LIVE UPDATE'}\n{'='*75}\n")
    
    file_count = 0
    for root, _, files in os.walk(VAULT_PATH):
        for file in files:
            if file.endswith(".md"):
                path = os.path.join(root, file)
                result = process_file(path)
                
                if result:
                    new_content, changes = result
                    file_count += 1
                    print(f"📄 {file}")
                    for c in changes:
                        print(f"   └─ {c['key']}: {c['msg']}")
                    
                    # SAFETY GATE
                    if not IS_DRY_RUN:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)

    print(f"\n{'='*75}\nSummary: {file_count} files analyzed.\n{'='*75}\n")

if __name__ == "__main__":
    run_vault_update()