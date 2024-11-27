import os
from pathlib import Path
import json
from openai import OpenAI
import re

client = OpenAI()

def query_openai(prompt, model_name="gpt-4o-mini", assistant_instructions="You are a helpful assistant."):
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": assistant_instructions},
            {"role": "user", "content": prompt}
        ]
    )
    return completion.choices[0].message.content

def get_metadata_files(corpora_dir):
    """Get all .txt.met files from the corpora directory"""
    metadata_files = []
    for root, dirs, files in os.walk(corpora_dir):
        for file in files:
            if file.endswith('.txt.met'):
                metadata_files.append(os.path.join(root, file))
    return metadata_files

def read_metadata(file_path):
    """Read and parse metadata file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_citation_prompt(metadata):
    """Create prompt for OpenAI to generate citation"""
    prompt = """Please convert the following metadata into a Chicago style citation in markdown format. Return ONLY the citation, no explanation or additional text:

Title: {title}
Author: {author}
Publisher: {publisher}
Year: {year}""".format(
        title=metadata.get('title', ''),
        author=metadata.get('author', ''),
        publisher=metadata.get('publisher', ''),
        year=metadata.get('publication_date', '')
    )
    return prompt

def clean_citation(citation):
    """Clean up the citation string"""
    # Remove any markdown formatting if present
    citation = re.sub(r'^\s*[\*_]+|[\*_]+\s*$', '', citation)
    # Remove any extra whitespace or newlines
    citation = citation.strip()
    return citation

def main():
    # Get path to corpora directory
    corpora_dir = Path("corpora_cited")
    
    # Get all metadata files
    metadata_files = get_metadata_files(corpora_dir)
    
    # Store citations
    citations = []
    
    # Process each metadata file
    for file_path in metadata_files:
        try:
            # Read metadata
            metadata = read_metadata(file_path)
            
            # Generate prompt
            prompt = generate_citation_prompt(metadata)
            
            # Get citation from OpenAI
            citation = query_openai(
                prompt,
                assistant_instructions="You are a citation generator. Return ONLY the Chicago style citation, no explanation or additional text."
            )
            
            # Clean citation
            # citation = clean_citation(citation)
            
            # Add to citations list
            citations.append(citation)
            
            print(f"Processed: {file_path}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Sort citations alphabetically
    citations.sort()
    
    # Create bibliography markdown
    bibliography = "# Bibliography\n\n"
    for citation in citations:
        bibliography += f"{citation}\n\n"
    
    # Save to file
    with open("bibliography.md", 'w', encoding='utf-8') as f:
        f.write(bibliography)
    
    print(f"\nProcessed {len(citations)} citations")
    print("Bibliography saved to bibliography.md")

if __name__ == "__main__":
    main()