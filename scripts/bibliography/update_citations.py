import re
import os
import shutil
from pathlib import Path

def update_citations(prospectus_path: str) -> tuple[set, str]:
    """
    Extract all citations and update them to use corpora_cited.
    Returns both the set of citations and the updated content.
    """
    citations = set()
    citation_pattern = r'\[([^\]]+?)\]\((\./)?corpora/(.*?)\)'
    
    with open(prospectus_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Find and process all citations
    matches = list(re.finditer(citation_pattern, content))
    
    # Work backwards through the matches to avoid offset issues
    for match in reversed(matches):
        text = match.group(1)  # The citation text
        path = match.group(3)  # The path after 'corpora/'
        
        # Create the new citation format
        new_citation = f'[{text}](./corpora_cited/{path})'
        
        # Update the content
        content = content[:match.start()] + new_citation + content[match.end():]
        
        # Store the citation information
        dir_path = os.path.dirname(f'corpora/{path}')
        citations.add((f'corpora/{path}', dir_path))
    
    # Write the updated content back to the file
    with open(prospectus_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'Updated {len(matches)} citations in {prospectus_path}')
    return citations, content

def copy_cited_files(citations: set):
    """Copy cited files and their metadata to corpora_cited directory."""
    # Create corpora_cited directory if it doesn't exist
    if not os.path.exists('corpora_cited'):
        os.makedirs('corpora_cited')
    
    for cited_file, dir_path in citations:
        # Create the directory structure
        new_dir = os.path.join('corpora_cited', dir_path.replace('corpora/', ''))
        os.makedirs(new_dir, exist_ok=True)
        
        # Copy the cited file
        if os.path.exists(cited_file):
            dest_file = cited_file.replace('corpora/', 'corpora_cited/')
            shutil.copy2(cited_file, dest_file)
            print(f'Copied {cited_file} to {dest_file}')
        
        # find the metadata file ends with .met
        dir_path = os.path.dirname(dir_path)
        for file in os.listdir(dir_path):
            print(file)
            if file.endswith('.met'):
                met_file = os.path.join(dir_path, file)
                # do one .. up the directory tree
                new_dir = os.path.dirname(new_dir)
                dest_met = os.path.join(new_dir, file)            
                shutil.copy2(met_file, dest_met)
                print(f'Copied {met_file} to {dest_met}')

def main():
    # Get cited files
    citations, _ =  update_citations('prospectus.md')
    print(f'Found {len(citations)} citations in prospectus')
    
    # Copy cited files and metadata
    copy_cited_files(citations)
    


if __name__ == '__main__':
    main()