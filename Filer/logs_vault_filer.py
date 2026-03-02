import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
DRY_RUN = False              
PROCESS_INBOX_ONLY = True  
VAULT_PATH = Path("/Volumes/ObsidianSync/Logs Vault") 
INBOX_PATH = VAULT_PATH / "01 - Filer"

# PROTECTIONS: Files to ignore or keep in place
CLEANUP_IGNORE = {".DS_Store", "workspace.json", "graph.json", "appearance.json"}
STAY_PUT_DIRS = {"Templater", ".obsidian", ".trash"}
# Extensions that the filer will NEVER touch
PROTECTED_EXTENSIONS = {".js", ".json", ".css", ".py", ".sh"} 
# Top-level folders that should never be deleted by cleanup
BASE_PERMANENT_DIRS = {"01 - Filer", "Templater", "Attachments", "Nexuses", ".obsidian"} 

def clean_filename(name):
    """Removes trailing duplicate counters like '-1' or '-2'."""
    cleaned = re.sub(r'(-\d+)+$', '', name)
    return cleaned, cleaned != name

def get_frontmatter(content):
    """Extracts front matter keys and values from Markdown files."""
    fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match: return {}
    data = {}
    for line in fm_match.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            data[k.strip().lower()] = v.strip().strip('"').strip("'").strip("[]")
    return data

def extract_year_markdown(filename, frontmatter=None):
    """Determines year from date_created metadata or filename."""
    if frontmatter:
        date_val = frontmatter.get('date_created', '')
        if len(date_val) >= 4 and date_val[:4].isdigit(): return date_val[:4]
    if filename[:4].isdigit(): return filename[:4]
    return str(datetime.now().year)

def organize_logs():
    vault_root = VAULT_PATH.resolve()
    move_count = 0
    
    # Define files to evaluate (Inbox only or Full Vault)
    files_to_process = list(vault_root.rglob("*")) if not PROCESS_INBOX_ONLY else [f for f in INBOX_PATH.iterdir() if f.is_file()]

    for file_path in files_to_process:
        # 1. Protection Checks
        if not file_path.is_file() or file_path.name in CLEANUP_IGNORE: continue
        if any(s_dir in file_path.parts for s_dir in STAY_PUT_DIRS): continue
        if file_path.suffix.lower() in PROTECTED_EXTENSIONS: continue
        
        cleaned_stem, was_sanitized = clean_filename(file_path.stem)
        base_name = cleaned_stem + file_path.suffix
        ext_lower = file_path.suffix.lower()
        dest_dir = None

        # 2. Markdown Categorization
        if ext_lower == ".md":
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                fm = get_frontmatter(content)
                doc_type = fm.get('type', '').lower()
                kind_raw = fm.get('kind', '').strip()
                
                # Standardize Kind branding
                if kind_raw.lower() == "timos": 
                    kind = "TimOS"
                elif kind_raw.lower() == "dailyitinerary":
                    kind = "DailyItinerary"
                else:
                    kind = kind_raw.capitalize()

                year_val = extract_year_markdown(base_name, fm)

                if "nexus" in doc_type:
                    # Nexuses stay in their isolated categorized branch
                    dest_dir = vault_root / "Nexuses" / f"{kind} Nexuses" / year_val
                elif "log entry" in doc_type:
                    # NEW SIMPLIFIED FOLDER PATTERN: [Kind] Logs / [Year] [Kind] Logs /
                    # Example: /Family Logs/2026 Family Logs/
                    kind_suffix = "Daily Itineraries" if kind == "DailyItinerary" else f"{kind} Logs"
                    folder_name = f"{year_val} {kind_suffix}"
                    dest_dir = vault_root / f"{kind} Logs" / folder_name
            except: continue
        
        # 3. Attachment Fallback (For PDFs, Images, etc.)
        if not dest_dir:
            dest_dir = vault_root / "Attachments" / (ext_lower.upper().replace('.', ''))

        final_target = (dest_dir / base_name).resolve()
        current_loc = file_path.resolve()

        # Skip if already in the right place
        if str(current_loc).lower() == str(final_target).lower() and not was_sanitized:
            continue
        
        # Avoid overwriting existing files if sanitized
        if was_sanitized and final_target.exists() and str(current_loc).lower() != str(final_target).lower():
            continue

        # Perform the move
        move_count += 1
        if not DRY_RUN:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(current_loc), str(final_target))

    print(f"Log Vault Filer v1.10: {'Perfect' if move_count == 0 else f'Moved {move_count} files'}.")

    # 4. Recursive Empty Folder Cleanup
    if not DRY_RUN:
        for root, dirs, files in os.walk(vault_root, topdown=False):
            curr = Path(root)
            if curr == vault_root: continue
            
            # Don't delete protected or root category folders
            is_permanent = curr.name in BASE_PERMANENT_DIRS
            is_log_root = curr.name.endswith(" Logs") or curr.name.endswith(" Nexuses")
            if is_permanent or is_log_root: continue
            
            if not any(curr.iterdir()): 
                try: curr.rmdir()
                except: pass

if __name__ == "__main__":
    organize_logs()