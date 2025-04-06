#!/usr/bin/env python3
import re
import sys

def analyze_footnote_sequence(file_path):
    # Read the content of the file
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Find all footnote references in the text (NOT followed by a colon)
    reference_pattern = r"\[\^(\d+(?:\.\d+)?)\](?!:)"
    references = list(re.finditer(reference_pattern, content))
    
    # Sort references by position in document
    references.sort(key=lambda x: x.start())
    
    # Find all footnote definitions (must have a colon)
    definition_pattern = r"\[\^(\d+(?:\.\d+)?)\]: (.+?)(?=\n\n|\n\[\^|\Z)"
    definitions = list(re.finditer(definition_pattern, content, re.DOTALL))
    
    # Map definitions for lookup
    def_map = {}
    for match in definitions:
        def_num = match.group(1)
        def_content = match.group(2).strip()
        def_pos = match.start()
        
        if def_num not in def_map:
            def_map[def_num] = []
        
        def_map[def_num].append({
            "content": def_content[:50] + "..." if len(def_content) > 50 else def_content,
            "position": def_pos
        })
    
    # Print out the sequence
    print("\nFOOTNOTE SEQUENCE ANALYSIS\n")
    print(f"{'Seq #':<8} {'Original #':<12} {'Position':<10} {'Definition Found':<20} {'Content Preview'}")
    print("-" * 120)
    
    # Track where we've already processed a definition
    processed_defs = {}
    
    for i, match in enumerate(references, 1):
        ref_num = match.group(1)
        position = match.start()
        
        # Check if there's a matching definition
        if ref_num in def_map and def_map[ref_num]:
            def_found = "Yes"
            def_preview = def_map[ref_num][0]["content"]
            # Only mark this definition as used if we haven't seen this ref_num before
            if ref_num not in processed_defs:
                processed_defs[ref_num] = True
                def_map[ref_num].pop(0)
        else:
            def_found = "NO DEFINITION"
            def_preview = ""
        
        print(f"{i:<8} {ref_num:<12} {position:<10} {def_found:<20} {def_preview}")
    
    # Print summary
    print("\nSUMMARY:")
    print(f"Total footnote references in sequence: {len(references)}")
    unused_defs = sum(len(defs) for defs in def_map.values())
    print(f"Unused footnote definitions: {unused_defs}")
    
    # Generate a sequential numbering plan
    print("\nSEQUENTIAL RENUMBERING PLAN:")
    print(f"{'Seq #':<8} {'Original #':<12} {'New #':<8}")
    print("-" * 35)
    
    next_number = 1
    for i, match in enumerate(references, 1):
        ref_num = match.group(1)
        new_num = next_number
        print(f"{i:<8} {ref_num:<12} {new_num:<8}")
        next_number += 1
    
    # Also generate a mapping of original numbers to their first occurrence number
    # This is useful for a more traditional footnote renumbering approach
    print("\nUNIQUE NUMBER RENUMBERING PLAN:")
    print(f"{'Original #':<12} {'New #':<8} {'Occurrences':<12}")
    print("-" * 35)
    
    # Track which original numbers map to which new numbers
    unique_numbers = {}
    occurrence_count = {}
    next_unique_num = 1
    
    for match in references:
        ref_num = match.group(1)
        if ref_num not in unique_numbers:
            unique_numbers[ref_num] = next_unique_num
            occurrence_count[ref_num] = 1
            next_unique_num += 1
        else:
            occurrence_count[ref_num] += 1
    
    # Sort by new number for display
    for ref_num, new_num in sorted(unique_numbers.items(), key=lambda x: x[1]):
        print(f"{ref_num:<12} {new_num:<8} {occurrence_count[ref_num]:<12}")
    
    print(f"\nTotal unique footnote numbers: {len(unique_numbers)}")
    print(f"Total footnote references: {len(references)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python footnote_sequence.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    analyze_footnote_sequence(file_path) 