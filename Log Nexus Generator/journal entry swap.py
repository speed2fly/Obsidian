import os
import re
from pathlib import Path

# --- CONFIGURATION ---
DRY_RUN = False  # Set to False to apply changes
VAULT_PATH = Path("/Volumes/ObsidianSync/Logs Vault")

def get_metadata(content):
    """Extracts kind and the month from date_created metadata."""
    fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match:
        return None, None
    
    metadata = {}
    for line in fm_match.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            metadata[k.strip().lower()] = v.strip().strip('"').strip("'")
    
    kind = metadata.get('kind', 'Personal').capitalize()
    if kind.lower() == "timos": kind = "TimOS"
    
    # Extract Month (MM) from YYYY-MM-DD
    date_val = metadata.get('date_created', '')
    month = date_val[5:7] if len(date_val) >= 7 else None
        
    return kind, month

def migrate_links():
    mode_status = "[DRY RUN]" if DRY_RUN else "[LIVE MODE]"
    print(f"--- {mode_status} Multi-Pattern Nexus Migrator v4.2 ---")
    
    change_count = 0
    
    # PATTERNS:
    # 1. Catch-all for Journal Entries (with/without MOC, dashes, or months)
    # This now captures:
    # [[2020 Journal Entries MOC]]
    # [[2019-03 - Journal Entries]]
    # [[2022 - Jun Journal Entries]]
    # [[2014 Journal Entries]]
    catch_all_pattern = re.compile(r'\[\[(\d{4})[^\]]*Journal Entries(?: MOC)?\]\]')

    for file_path in VAULT_PATH.rglob("*.md"):
        if any(part.startswith('.') or part == "Templater" for part in file_path.parts):
            continue
            
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        if "Journal Entries" not in content:
            continue

        kind, meta_month = get_metadata(content)
        if not kind or not meta_month:
            print(f"SKIP: {file_path.name} (Missing Metadata)")
            continue

        def replacement_logic(match):
            year = match.group(1) 
            return f"[[{year}-{meta_month} - {kind} Logs]]"

        new_content, count = catch_all_pattern.subn(replacement_logic, content)

        if count > 0:
            change_count += count
            print(f"MIGRATING: {file_path.name} ({count} links)")
            
            if not DRY_RUN:
                file_path.write_text(new_content, encoding='utf-8')

    print(f"\nMigration complete. {change_count} links updated.")

if __name__ == "__main__":
    migrate_links()