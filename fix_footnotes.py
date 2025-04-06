#!/usr/bin/env python3
import re
import sys

def fix_footnotes(file_path):
    # Read the content of the file
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Initialize our counter for sequential numbering
    counter = 1
    
    # Keep track of how many references and definitions we've replaced
    refs_replaced = 0
    defs_replaced = 0
    
    # Make a copy of the content that we'll update
    updated_content = content
    
    # Offset to adjust positions as we make changes
    offset = 0
    
    # Find all footnote references in the text in order of appearance
    reference_pattern = r"\[\^(\d+(?:\.\d+)?)\]"
    for match in re.finditer(reference_pattern, content):
        # Get the current footnote reference data
        original_ref = match.group(0)  # The entire reference, e.g., [^1]
        ref_num = match.group(1)       # Just the number, e.g., 1
        ref_pos = match.start()        # Position in the original content
        
        # Create the new reference with the current counter
        new_ref = f"[^{counter}]"
        
        # Update the reference in our content
        adjusted_pos = ref_pos + offset
        updated_content = updated_content[:adjusted_pos] + new_ref + updated_content[adjusted_pos + len(original_ref):]
        
        # Update our offset
        offset += len(new_ref) - len(original_ref)
        refs_replaced += 1
        
        # Now find the corresponding definition for this reference
        def_pattern = r"\[\^" + re.escape(ref_num) + r"\]: (.+?)(?=\n\n|\n\[\^|\Z)"
        def_match = re.search(def_pattern, content, re.DOTALL)
        
        if def_match:
            # Get the definition data
            original_def = def_match.group(0)  # The entire definition
            def_content = def_match.group(1)   # Just the content
            def_pos = def_match.start()        # Position in the original content
            
            # Create the new definition
            new_def = f"[^{counter}]: {def_content}"
            
            # Find the position in the updated content
            # We need to search for the original definition in our updated content
            updated_def_pos = updated_content.find(original_def)
            
            if updated_def_pos != -1:
                # Replace the definition in our updated content
                updated_content = updated_content[:updated_def_pos] + new_def + updated_content[updated_def_pos + len(original_def):]
                offset = len(updated_content) - len(content)  # Recalculate offset
                defs_replaced += 1
        
        # Increment the counter for the next footnote
        counter += 1
    
    # Write the updated content back to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(updated_content)
    
    return {
        "total_footnotes": counter - 1,
        "references_replaced": refs_replaced,
        "definitions_replaced": defs_replaced
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_footnotes.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    stats = fix_footnotes(file_path)
    print(f"Footnote renumbering complete!")
    print(f"Total footnotes: {stats['total_footnotes']}")
    print(f"References replaced: {stats['references_replaced']}")
    print(f"Definitions replaced: {stats['definitions_replaced']}") 