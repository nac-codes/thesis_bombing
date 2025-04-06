#!/usr/bin/env python3
import re
import sys

def renumber_footnotes(file_path):
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
    
    # Create a mapping of original footnote numbers to their definitions
    def_map = {}
    for match in definitions:
        def_num = match.group(1)
        def_content = match.group(2)
        def_start = match.start()
        def_end = match.end()
        
        if def_num not in def_map:
            def_map[def_num] = []
        
        def_map[def_num].append({
            "content": def_content,
            "start": def_start,
            "end": def_end,
            "used": False  # Track if this definition has been used
        })
    
    # Create a sequential numbering plan with original position tracking
    sequential_map = []
    for i, match in enumerate(references, 1):
        ref_num = match.group(1)
        ref_start = match.start()
        ref_end = match.end()
        sequential_map.append({
            "orig_num": ref_num,
            "new_num": i,
            "ref_start": ref_start,
            "ref_end": ref_end
        })
    
    # Now we need to match each reference with its corresponding definition
    # We'll use a dict to track which definitions we've already used
    processed_defs = {}
    
    # Create a plan for which definitions to update
    def_updates = []
    for item in sequential_map:
        orig_num = item["orig_num"]
        new_num = item["new_num"]
        
        # Skip if we don't have a definition for this number
        if orig_num not in def_map or not def_map[orig_num]:
            continue
        
        # Get the next unused definition for this number
        def_index = 0
        while def_index < len(def_map[orig_num]) and def_map[orig_num][def_index]["used"]:
            def_index += 1
        
        if def_index < len(def_map[orig_num]):
            def_data = def_map[orig_num][def_index]
            def_data["used"] = True  # Mark as used
            
            def_updates.append({
                "orig_num": orig_num,
                "new_num": new_num,
                "start": def_data["start"],
                "end": def_data["end"],
                "content": def_data["content"]
            })
    
    # Now apply all the updates, starting from the end to avoid position shifting
    # First, sort all updates by their position in reverse order
    all_updates = sequential_map + def_updates
    all_updates.sort(key=lambda x: x.get("ref_start", x.get("start")), reverse=True)
    
    # Apply the updates
    for update in all_updates:
        if "ref_start" in update:  # This is a reference update
            start = update["ref_start"]
            end = update["ref_end"]
            new_ref = f"[^{update['new_num']}]"
        else:  # This is a definition update
            start = update["start"]
            end = update["end"]
            new_def = f"[^{update['new_num']}]: {update['content']}"
            
        # Replace the old footnote with the new one
        if "ref_start" in update:
            content = content[:start] + new_ref + content[end:]
        else:
            content = content[:start] + new_def + content[end:]
    
    # Write the updated content back to the file
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)
    
    # Return statistics
    return {
        "total_references": len(sequential_map),
        "total_definitions_updated": len(def_updates),
        "total_unique_numbers": len(set(item["orig_num"] for item in sequential_map))
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python renumber_footnotes.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    stats = renumber_footnotes(file_path)
    print(f"Footnote renumbering complete!")
    print(f"Total references updated: {stats['total_references']}")
    print(f"Total definitions updated: {stats['total_definitions_updated']}")
    print(f"Total unique original footnote numbers: {stats['total_unique_numbers']}") 