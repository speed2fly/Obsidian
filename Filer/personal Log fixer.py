import os
import re
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
DRY_RUN = False  # Set to False to actually modify the files
VAULT_PATH = Path("/Volumes/ObsidianSync/My Vault")
TARGET_DOMAIN = "Personal"

def fix_metadata():
    mode_status = "[DRY RUN - NO CHANGES]" if DRY_RUN else "[LIVE MODE - APPLYING FIXES]"
    print(f"--- {mode_status} ---")
    
    # We target the Personal folder specifically to be safe
    personal_path = VAULT_PATH / TARGET_DOMAIN
    if not personal_path.exists():
        print(f"Error: Could not find path {personal_path}")
        return

    # Table Header for feedback
    header = f"| {'File Name':<45} | {'Action':<20} |"
    divider = f"| {'-'*45} | {'-'*20} |"
    print(header)
    print(divider)

    fix_count = 0
    
    for file_path in personal_path.rglob("*.md"):
        # Rule 1: Filename must NOT contain "Daily Itinerary"
        if "Daily Itinerary" in file_path.name:
            continue
            
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Rule 2: Front matter must contain exactly the mistake pattern
            # We look for the block specifically to avoid touching body text
            fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
            if not fm_match:
                continue
                
            fm_block = fm_match.group(0)
            
            # Check for the specific problematic combination
            if 'type: Log Entry' in fm_block and 'kind: DailyItinerary' in fm_block:
                # Prepare the fix
                new_fm_block = fm_block.replace('kind: DailyItinerary', 'kind: Personal')
                
                print(f"| {file_path.name[:42]:<45} | Updated to 'Personal' |")
                fix_count += 1
                
                if not DRY_RUN:
                    new_content = content.replace(fm_block, new_fm_block)
                    file_path.write_text(new_content, encoding='utf-8')
                    
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    print(f"\n{mode_status} Complete. {fix_count} files corrected.")

if __name__ == "__main__":
    fix_metadata()