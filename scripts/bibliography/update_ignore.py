import re
import os
from pathlib import Path

def extract_citations(prospectus_path: str) -> set:
    """Extract all citations from the prospectus markdown file."""
    citations = set()
    citation_pattern = r'\[.*?\]\((.*?)\)'
    
    with open(prospectus_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # Find all matches using regex
        matches = re.finditer(citation_pattern, content)
        for match in matches:
            citation_path = match.group(1)
            # Only include corpora citations
            if 'corpora' in citation_path:
                citations.add(citation_path)
    
    return citations

def get_all_corpora_files(corpora_dir: str) -> set:
    """Get all files in the corpora directory."""
    all_files = set()
    for root, _, files in os.walk(corpora_dir):
        for file in files:
            if file.endswith('.met'):
                continue
            # Convert to relative path from project root
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path)
            all_files.add(relative_path)
    
    return all_files

def update_gitignore(files_to_ignore: set):
    """Update .gitignore with files to ignore while preserving other entries."""
    # Read existing .gitignore
    existing_entries = set()
    if os.path.exists('.gitignore'):
        with open('.gitignore', 'r', encoding='utf-8') as f:
            existing_entries = {line.strip() for line in f if line.strip() 
                              and not line.strip().startswith('corpora/')}
    
    # Combine existing non-corpora entries with new corpora entries
    all_entries = existing_entries | files_to_ignore
    
    # Write updated .gitignore
    with open('.gitignore', 'w', encoding='utf-8') as f:
        f.write('# Auto-generated corpora ignores\n')
        # Write corpora entries first
        for entry in sorted(files_to_ignore):
            f.write(f'{entry}\n')
        # Write other existing entries
        if existing_entries:
            f.write('\n# Other entries\n')
            for entry in sorted(existing_entries):
                f.write(f'{entry}\n')

def main():
    # Paths
    prospectus_path = 'prospectus.md'
    corpora_dir = 'corpora'
    
    # Get cited files
    cited_files = extract_citations(prospectus_path)
    print(f'Found {len(cited_files)} citations in prospectus')
    
    # Get all corpora files
    all_files = get_all_corpora_files(corpora_dir)
    print(f'Found {len(all_files)} total files in corpora')
    
    # Determine which files to ignore (all files minus cited ones)
    files_to_ignore = all_files - cited_files
    print(f'Adding {len(files_to_ignore)} files to .gitignore')
    
    # Update .gitignore
    update_gitignore(files_to_ignore)
    print('Updated .gitignore successfully')

if __name__ == '__main__':
    main()