import os
import re
from pathlib import Path

# --- CONFIGURATION ---
VAULT_PATH = Path("/Volumes/ObsidianSync/Logs Vault")
TEMPLATER_PATH = VAULT_PATH / "Templater"
DRY_RUN = False  # Ready for Live Mode per your previous success

def update_templates():
    print(f"--- Templater Metadata Updater v4.2 ---")
    
    update_count = 0

    for file_path in TEMPLATER_PATH.rglob("*.md"):
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        # 1. Extract the Kind from the template
        kind_match = re.search(r'kind:\s*(\w+)', content, re.IGNORECASE)
        if not kind_match:
            continue
            
        kind_raw = kind_match.group(1).strip()
        
        # 2. Match the specific Nexus naming conventions
        if kind_raw.lower() in ["dailyitinerary", "daily itinerary"]:
            nexus_suffix = "- Daily Itineraries"
        elif kind_raw.lower() in ["dailyscore", "daily score"]:
            nexus_suffix = "- Daily Scores"
        elif kind_raw.lower() == "timos":
            nexus_suffix = "TimOS Log Entries"
        else:
            # Matches Family, House, Personal, etc.
            nexus_suffix = f"{kind_raw.capitalize()} Log Entries"

        # 3. Build the QUOTED Templater Wiki Link
        # part_of: "[[<% tp.date.now("YYYY") %> Family Log Entries]]"
        nexus_link = f'part_of: "[[<% tp.date.now(\"YYYY\") %> {nexus_suffix}]]"'

        # 4. Inject or Update the part_of key
        if "part_of:" in content:
            # Replaces existing part_of line regardless of its current value
            new_content = re.sub(r'part_of:.*', nexus_link, content)
        else:
            # Injects right after the 'kind:' line for clean organization
            new_content = re.sub(r'(kind:.*)', r'\1\n' + nexus_link, content)

        if new_content != content:
            update_count += 1
            print(f"UPDATED: {file_path.name} -> {nexus_link}")
            if not DRY_RUN:
                file_path.write_text(new_content, encoding='utf-8')

    print(f"\nTask complete. {update_count} templates updated in the Templater folder.")

if __name__ == "__main__":
    update_templates()