import os
import re
from pathlib import Path
from datetime import datetime

# --- CONFIGURATION ---
DRY_RUN = True  # Set to False to apply changes to files
VAULT_PATH = Path("/Volumes/ObsidianSync/My Vault")
REPORT_NAME = "link_cleanup_results.txt"

def strip_link_paths(content):
    """
    Finds wiki links in front matter key-value pairs and strips paths.
    Matches: [[folder/sub/File]] or "[[folder/sub/File]]"
    """
    # pattern captures everything between [[ and the last / as group 1
    # and the filename as group 2.
    pattern = r'\[\[([^\]]*/)([^\]]+)\]\]'
    
    # We use a lambda to ensure we don't accidentally mess up 
    # non-link text, though this regex is quite specific to wiki links.
    cleaned = re.sub(pattern, r'[[\2]]', content)
    return cleaned

def generate_table_row(before, after, path):
    return f"| {before:<30} | {after:<30} | {path} |"

def clean_vault_metadata():
    mode_status = "[DRY RUN - NO CHANGES]" if DRY_RUN else "[LIVE MODE - MODIFYING CONTENT]"
    print(f"--- {mode_status} ---\n")
    
    table_header = [
        "| " + "before name".ljust(30) + " | " + "after name".ljust(30) + " | " + "path to the file".ljust(40) + " |",
        "| " + "-"*30 + " | " + "-"*30 + " | " + "-"*40 + " |"
    ]
    
    results = []
    change_count = 0

    # Scan all markdown files in the vault
    for file_path in VAULT_PATH.rglob("*.md"):
        try:
            # We only want to look at the front matter block
            original_content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Find the front matter block (between the first two ---)
            fm_match = re.search(r'^---\s*\n(.*?)\n---\s*\n', original_content, re.DOTALL)
            if not fm_match:
                continue
                
            fm_block = fm_match.group(0)
            cleaned_fm = strip_link_paths(fm_block)
            
            if fm_block != cleaned_fm:
                # Find the specific changes for the table feedback
                # This regex helps us identify what exactly was stripped for the "before/after" view
                matches = re.findall(r'\[\[([^\]]*/)([^\]]+)\]\]', fm_block)
                for path_prefix, filename in matches:
                    before_val = f"[[{path_prefix}{filename}]]"
                    after_val = f"[[{filename}]]"
                    rel_path = file_path.relative_to(VAULT_PATH)
                    results.append(generate_table_row(before_val, after_val, str(rel_path)))
                
                change_count += 1
                if not DRY_RUN:
                    new_content = original_content.replace(fm_block, cleaned_fm)
                    file_path.write_text(new_content, encoding='utf-8')
                    
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    # Output results
    output = "\n".join(table_header + results)
    print(output)
    
    # Save to report file
    report_file = VAULT_PATH / REPORT_NAME
    with open(report_file, "w") as f:
        f.write(f"METADATA LINK CLEANUP RESULTS - {datetime.now()}\n")
        f.write(f"Files Modified: {change_count}\n\n")
        f.write(output)

    print(f"\nScan complete. {change_count} files flagged for updates. Results saved to {REPORT_NAME}.")

if __name__ == "__main__":
    clean_vault_metadata()