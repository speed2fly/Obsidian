import os
import re
from pathlib import Path

# --- CONFIGURATION ---
DRY_RUN = False  # LIVE MODE ENGAGED
VAULT_PATH = Path("/Volumes/ObsidianSync/Logs Vault")

def get_metadata(content):
    fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not fm_match: return None, None
    
    metadata = {}
    for line in fm_match.group(1).split('\n'):
        if ':' in line:
            k, v = line.split(':', 1)
            metadata[k.strip().lower()] = v.strip().strip('"').strip("'")
    
    kind_raw = metadata.get('kind', 'Personal')
    # Standardization Logic
    if kind_raw.lower() in ["daily itinerary", "dailyitinerary"]: kind = "DailyItinerary"
    elif kind_raw.lower() in ["daily score", "dailyscore"]: kind = "DailyScore"
    elif kind_raw.lower() == "timos": kind = "TimOS"
    elif kind_raw.lower() == "overlanding": kind = "Overlander" # Mapping Overlanding -> Overlander
    else: kind = kind_raw.capitalize()
    
    year = metadata.get('date_created', '')[:4]
    return kind, year

def migrate_links():
    print(f"--- LIVE MODE: Link Migrator v3.5 ---")
    
    update_count = 0

    # TASK 1: The Space-Sensitive Outlier Pattern
    # Matches [[ 2023...]] or [[2023 ...]] with potential extra spaces
    outlier_pattern = re.compile(r'\[\[\s*(\d{4})\s*.*?Log Entries\s*\]\]', re.IGNORECASE)

    # TASK 2: General Legacy Links (Journal Entries, old monthly formats)
    legacy_pattern = re.compile(r'\[\[\d{4} Journal Entries\]\]|\[\[\d{4}-.*?Logs\]\]')

    for file_path in VAULT_PATH.rglob("*.md"):
        if any(part.startswith('.') or part == "Templater" for part in file_path.parts):
            continue
            
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        kind, year = get_metadata(content)
        
        if not kind or not year: continue

        new_content = content
        was_modified = False

        # Apply target determination based on kind
        if kind == "DailyItinerary":
            target = f"[[{year} - Daily Itineraries]]"
        elif kind == "DailyScore":
            target = f"[[{year} - Daily Scores]]"
        else:
            target = f"[[{year} {kind} Log Entries]]"

        # Replace any variation of "Log Entries" links (including the spaced outliers)
        new_content, count1 = outlier_pattern.subn(target, new_content)
        # Replace legacy journal/monthly formats
        new_content, count2 = legacy_pattern.subn(target, new_content)
        
        if count1 > 0 or count2 > 0: 
            was_modified = True

        # Task 3: The Daily Score Injection
        if kind == "DailyScore":
            score_link = f"\n\n[[{year} - Daily Scores]]"
            new_content += score_link
            was_modified = True

        if was_modified:
            update_count += 1
            print(f"FIXED: {file_path.name} | Kind: {kind}")
            if not DRY_RUN:
                file_path.write_text(new_content, encoding='utf-8')

    print(f"\nMigration complete. {update_count} files updated in Live Mode.")

if __name__ == "__main__":
    migrate_links()