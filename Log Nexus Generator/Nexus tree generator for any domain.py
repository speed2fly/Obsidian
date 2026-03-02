import os
import re
from datetime import datetime
from pathlib import Path

# --- CONFIGURATION ---
TARGET_DOMAIN = "Library"  # Set your domain here
TARGET_DIRECTORY = r"/Volumes/ObsidianSync/My Vault/Library/Markdown Files/2026"
DRY_RUN = False  # Defaulting to True per instructions

DV_MARKER = "\n\n%%DATAVIEW_QUERY_PLACEHOLDER%%\n"

def is_valid_filename(name):
    """Checks if a string can be used as a filename on most OSs."""
    # Forbidden characters: \ / : * ? " < > |
    return not bool(re.search(r'[\\/*?:"<>|]', name))

def get_frontmatter_value(content, key):
    fm_match = re.search(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not fm_match: return None
    fm_text = fm_match.group(1)
    match = re.search(rf"^{key}:\s*(.*?)\s*$", fm_text, re.MULTILINE)
    if match: return match.group(1).strip().strip('"').strip("'")
    return None

def update_part_of_quoted(content, target_link):
    """Standardizes malformed part_of entries and appends the new target_link."""
    quoted_link = f'"{target_link}"'
    
    # Detect existing part_of block
    match = re.search(r"^part_of:(.*?)\n((?:\s*- .*\n?)*)", content, re.MULTILINE)
    
    if match:
        inline_val = match.group(1).strip()
        existing_list = match.group(2)
        clean_inline = inline_val.strip('"').strip("'")
        
        if target_link in clean_inline or target_link in existing_list:
            if not inline_val:
                return content, False 

        new_list_items = []
        if inline_val:
            val = inline_val if inline_val.startswith('"') else f'"{inline_val}"'
            new_list_items.append(f"  - {val}")
            
        for line in existing_list.split('\n'):
            if line.strip():
                new_list_items.append(line.rstrip())
        
        if not any(target_link in item for item in new_list_items):
            new_list_items.append(f"  - {quoted_link}")
            
        replacement = "part_of:\n" + "\n".join(new_list_items) + "\n"
        new_content = re.sub(r"^part_of:.*?\n(?:\s*- .*\n?)*", replacement, content, count=1, flags=re.MULTILINE)
        return new_content, True

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            fm_content = parts[1].rstrip() + f'\npart_of:\n  - {quoted_link}'
            return f"---{fm_content}\n---{parts[2]}", True
            
    return content, False

def run_nexus_sync():
    path = Path(TARGET_DIRECTORY).expanduser().resolve()
    if not path.exists():
        print(f"ERROR: Directory '{path}' not found.")
        return

    # User Feedback Header
    mode_text = "DRY RUN (No changes will be saved)" if DRY_RUN else "LIVE MODIFICATION MODE"
    print("="*60)
    print(f" RUNNING IN: {mode_text}")
    print("="*60)

    root_name = f"Origin - {TARGET_DOMAIN}.md"
    print(f"\n>>> Starting Normalizing Sync for Domain: [{TARGET_DOMAIN}]")
    
    all_markdown_files = [f for f in path.iterdir() if f.suffix.lower() == ".md"]
    
    # 1. ROOT CHECK
    root_path = path / root_name
    if not root_path.exists():
        print(f"[PLAN] Create Root Nexus: {root_name}")
        if not DRY_RUN:
            content = (f"---\ndate_created: {datetime.now().strftime('%Y-%m-%d')}\ndomain: {TARGET_DOMAIN}\n"
                       f"type: Nexus\nkind: Origin\npart_of:\n  - \"[[Origins]]\"\nstatus:\n---\n{DV_MARKER}")
            with open(root_path, 'w', encoding='utf-8') as f: f.write(content)

    # 2. DISCOVERY & VALIDATION
    valid_files = []
    found_kinds = set()

    for file in all_markdown_files:
        if file.name == root_name or file.name.endswith(" Notes.md"):
            continue
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
        except: continue
        
        node_kind = get_frontmatter_value(content, "kind")
        node_type = get_frontmatter_value(content, "type")
        
        if node_kind and node_kind != "Origin" and node_type != "Nexus":
            # SKIP FILES WITH ILLEGAL KIND FILENAMES
            if not is_valid_filename(node_kind):
                print(f"[SKIP] Illegal 'kind' characters in '{file.name}': ({node_kind})")
                continue
                
            found_kinds.add(node_kind)
            valid_files.append((file, content, node_kind))

    # 3. CHILD NEXUS CHECK
    for k in found_kinds:
        nexus_name = f"{k} Notes.md"
        nexus_path = path / nexus_name
        
        if not nexus_path.exists():
            print(f"[PLAN] Create Child Nexus: {nexus_name}")
            if not DRY_RUN:
                content = (f"---\ndate_created: {datetime.now().strftime('%Y-%m-%d')}\ndomain: {TARGET_DOMAIN}\n"
                           f"type: Nexus\nkind: Aggregation\npart_of:\n  - \"[[Origin - {TARGET_DOMAIN}]]\"\nstatus:\n---\n{DV_MARKER}")
                with open(nexus_path, 'w', encoding='utf-8') as f: f.write(content)

    # 4. NORMALIZING ROLLUP
    print(f"\n>>> Evaluating {len(valid_files)} valid files...")
    for file_path, content, node_kind in valid_files:
        target_link = f"[[{node_kind} Notes]]"
        new_content, changed = update_part_of_quoted(content, target_link)
        
        if changed:
            print(f"[ACTION] Standardize & Append: {file_path.name} -> \"{target_link}\"")
            if not DRY_RUN:
                with open(file_path, 'w', encoding='utf-8') as f: f.write(new_content)

    print(f"\n--- Sync Complete ---")

if __name__ == "__main__":
    run_nexus_sync()