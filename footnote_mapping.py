#!/usr/bin/env python3
import re
import sys
from collections import defaultdict

def analyze_footnotes(file_path):
    # Read the content of the file
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Find all footnote references in the text
    reference_pattern = r"\[\^(\d+(?:\.\d+)?)\]"
    references = re.finditer(reference_pattern, content)
    
    # Track where each footnote number appears in the document
    ref_positions = defaultdict(list)
    
    for match in references:
        ref_num = match.group(1)  # The footnote number
        position = match.start()   # Position in the document
        ref_positions[ref_num].append(position)
    
    # Find all footnote definitions
    definition_pattern = r"\[\^(\d+(?:\.\d+)?)\]: (.+?)(?=\n\n|\n\[\^|\Z)"
    definitions = re.finditer(definition_pattern, content, re.DOTALL)
    
    # Track all definitions
    def_info = {}
    
    for match in definitions:
        def_num = match.group(1)  # The footnote number
        def_content = match.group(2).strip()  # The definition content
        position = match.start()   # Position in the document
        
        # Store the first ~30 characters of content and position
        def_info[def_num] = {
            "content": def_content[:50] + "..." if len(def_content) > 50 else def_content,
            "position": position
        }
    
    # Print out the mapping
    print("\nFOOTNOTE MAPPING ANALYSIS\n")
    print(f"{'Footnote #':<12} {'References':<15} {'Definition':<50} {'Def Preview'}")
    print("-" * 120)
    
    # Sort footnote numbers naturally (1, 1.5, 2, 10 instead of 1, 10, 1.5, 2)
    def natural_sort_key(s):
        if '.' in s:
            return float(s)
        return int(s)
    
    footnote_numbers = sorted(set(list(ref_positions.keys()) + list(def_info.keys())), 
                             key=natural_sort_key)
    
    for num in footnote_numbers:
        ref_count = len(ref_positions.get(num, []))
        ref_status = f"{ref_count} instance(s)"
        
        if num in def_info:
            def_status = "Found at position " + str(def_info[num]["position"])
            def_preview = def_info[num]["content"]
        else:
            def_status = "MISSING"
            def_preview = ""
            
        print(f"{num:<12} {ref_status:<15} {def_status:<50} {def_preview}")
    
    # Print summary
    print("\nSUMMARY:")
    print(f"Total unique footnote numbers: {len(footnote_numbers)}")
    print(f"Total footnote references: {sum(len(pos) for pos in ref_positions.values())}")
    print(f"Total footnote definitions: {len(def_info)}")
    
    # Check for issues
    missing_defs = [num for num in ref_positions if num not in def_info]
    if missing_defs:
        print(f"\nWARNING: {len(missing_defs)} footnote reference(s) have no definition: {', '.join(missing_defs)}")
    
    missing_refs = [num for num in def_info if num not in ref_positions]
    if missing_refs:
        print(f"\nWARNING: {len(missing_refs)} footnote definition(s) have no reference: {', '.join(missing_refs)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python footnote_mapping.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    analyze_footnotes(file_path) 