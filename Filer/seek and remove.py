import os
import re
import shutil
from pathlib import Path

# --- CONFIGURATION ---
DRY_RUN = False  # Set to False to actually move the files
VAULT_PATH = Path("/Volumes/ObsidianSync/Logs Vault")
REMOVE_ME_PATH = VAULT_PATH / "99 - Remove Me"

def get_frontmatter(content):
    fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match: return {}
    data = {}
    for line in fm_match.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            data[k.strip().lower()] = v.strip().strip('"').strip("'").strip("[]")
    return data

def hunt_rogues():
    mode_status = "[DRY RUN]" if DRY_RUN else "[LIVE MODE]"
    print(f"--- {mode_status} Rogue Itinerary Hunter ---")
    
    if not DRY_RUN:
        REMOVE_ME_PATH.mkdir(parents=True, exist_ok=True)

    found_count = 0
    # Scan the entire vault for potential rogues
    for file_path in VAULT_PATH.rglob("*.md"):
        # Rule 1: Must have 'Daily Itineraries' in the filename
        if "Daily Itineraries" not in file_path.name:
            continue
            
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            fm = get_frontmatter(content)
            
            # Rule 2: Must have 'kind: personal' (the rogue signature)
            # and/or the specific date_created you mentioned
            kind = fm.get('kind', '').lower()
            date_created = fm.get('date_created', '')
            
            is_rogue = (kind == "personal") or (date_created == "2025-01-23")

            if is_rogue:
                found_count += 1
                target_path = REMOVE_ME_PATH / file_path.name
                
                # Handle potential name collisions in the Remove Me folder
                if target_path.exists():
                    target_path = REMOVE_ME_PATH / f"{file_path.stem}_{found_count}{file_path.suffix}"

                print(f"FOUND ROGUE: {file_path.relative_to(VAULT_PATH)}")
                print(f"   Metadata: kind={kind}, date={date_created}")
                
                if not DRY_RUN:
                    shutil.move(str(file_path), str(target_path))
                    print(f"   ACTION: Moved to {REMOVE_ME_PATH.name}")
                    
        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    print(f"\nScan complete. Total rogues identified: {found_count}")

if __name__ == "__main__":
    hunt_rogues()