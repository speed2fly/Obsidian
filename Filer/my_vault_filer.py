import os
import re
import shutil
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
DRY_RUN = False              
PROCESS_INBOX_ONLY = True  
VAULT_PATH = Path("/Volumes/ObsidianSync/My Vault")
INBOX_PATH = VAULT_PATH / "01 - Filer"
REPORT_NAME = "dry_run_results.txt"

CLEANUP_IGNORE = {".DS_Store"}
STAY_PUT_DIRS = {"Templater"}
PERMANENT_DIRS = {"01 - Filer", "Templater", "00 - Bases", "00 - Canvases", "Daily Scores"}
PROTECTED_EXTENSIONS = {".js", ".json", ".css"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg", ".webp", ".heic"}
ROOT_EXCLUSIONS = {"Next Week.md", "Rest of Week.md", "Today.md", "Tomorrow.md", REPORT_NAME}

def clean_filename(name):
    cleaned = re.sub(r'(-\d+)+$', '', name)
    return cleaned, cleaned != name

def get_frontmatter(content):
    fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match: return {}
    data = {}
    for line in fm_match.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            data[k.strip().lower()] = v.strip().strip('"').strip("'").strip("[]")
    return data

def get_unique_path(target_path):
    if not target_path.exists(): return target_path
    stem, suffix, parent = target_path.stem, target_path.suffix, target_path.parent
    counter = 1
    while True:
        new_path = parent / f"{stem}-{counter}{suffix}"
        if not new_path.exists(): return new_path
        counter += 1

def extract_year_markdown(filename, frontmatter=None):
    """Prioritizes 'date_created' per User Standard."""
    if frontmatter:
        # Standardized to your specific key: date_created
        date_val = frontmatter.get('date_created', '')
        if len(str(date_val)) >= 4 and str(date_val)[:4].isdigit(): 
            return str(date_val)[:4]
            
    # Fallback to filename or current year
    if filename[:4].isdigit(): return filename[:4]
    return str(datetime.now().year)

def organize_vault():
    mode_status = "[DRY RUN]" if DRY_RUN else "[LIVE MODE]"
    print(f"--- {mode_status} ---")
    
    vault_root = VAULT_PATH.resolve()
    if not vault_root.exists():
        print(f"CRITICAL ERROR: Path does not exist. Check mount for '{VAULT_PATH}'")
        return

    # Targeting logic
    if PROCESS_INBOX_ONLY:
        files_to_process = [f for f in INBOX_PATH.iterdir() if f.is_file()]
    else:
        files_to_process = list(vault_root.rglob("*"))

    print(f"Evaluating {len(files_to_process)} items...")

    move_count = 0
    for file_path in files_to_process:
        if not file_path.is_file() or file_path.name in CLEANUP_IGNORE or file_path.name in ROOT_EXCLUSIONS: continue
        if any(s_dir in file_path.parts for s_dir in STAY_PUT_DIRS): continue
        if file_path.suffix.lower() in PROTECTED_EXTENSIONS: continue

        cleaned_stem, was_sanitized = clean_filename(file_path.stem)
        base_name = cleaned_stem + file_path.suffix
        ext_lower = file_path.suffix.lower()
        dest_dir = None

        # 1. ROUTING
        if ext_lower in [".canvas", ".base"]:
            dest_dir = vault_root / ("00 - Canvases" if ext_lower == ".canvas" else "00 - Bases")
        elif ext_lower == ".md":
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                fm = get_frontmatter(content)
                domain = fm.get('domain', 'Unsorted').strip()
                kind = fm.get('kind', '').strip()
                
                # Check for Log metadata - these should be moved manually to the Logs Vault
                if kind in ["Log Entry", "Daily Itinerary"]:
                    print(f"SKIPPING LOG: {file_path.name} (Please move to Logs Vault Inbox)")
                    continue

                if "base" in fm.get('type', ''): dest_dir = vault_root / "00 - Bases"
                elif "canvas" in fm.get('type', ''): dest_dir = vault_root / "00 - Canvases"
                elif kind == "DailyScore": dest_dir = vault_root / "Daily Scores" / extract_year_markdown(base_name, fm)
                else: dest_dir = vault_root / domain / "Markdown Files" / extract_year_markdown(base_name, fm)
            except Exception as e: 
                print(f"Error reading {file_path.name}: {e}")
                continue
        
        if not dest_dir:
            dest_dir = vault_root / "Other Files" / (ext_lower.upper().replace('.', '') if ext_lower not in IMAGE_EXTENSIONS else "images")

        # 2. EXECUTION
        final_target = (dest_dir / base_name).resolve()
        current_loc = file_path.resolve()

        if str(current_loc).lower() == str(final_target).lower() and not was_sanitized:
            continue
            
        move_count += 1
        if not DRY_RUN:
            dest_dir.mkdir(parents=True, exist_ok=True)
            final_dest = get_unique_path(final_target)
            print(f"Moving: {file_path.name} -> {dest_dir.relative_to(vault_root)}")
            shutil.move(str(current_loc), str(final_dest))

    print(f"\nScan complete. {move_count} moves performed.")

if __name__ == "__main__":
    organize_vault()