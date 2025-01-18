import boto3
import logging
from pathlib import Path
from collections import defaultdict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_folder_structure(objects):
    """Create a nested dictionary representing the folder structure."""
    folder_structure = defaultdict(lambda: defaultdict(list))
    base_url = "https://bomberdata.s3.us-east-1.amazonaws.com/"
    
    for obj in objects:
        key = obj['Key']
        # Split the path into parts
        parts = key.split('/')
        
        if len(parts) >= 2:  # Has at least one folder
            main_folder = parts[0]
            if len(parts) == 2:  # File in root of main folder
                folder_structure[main_folder]['']['files'].append((parts[1], base_url + key))
            else:  # File in subfolder
                subfolder = '/'.join(parts[1:-1])
                folder_structure[main_folder][subfolder].append((parts[-1], base_url + key))

    return folder_structure

def generate_markdown(folder_structure):
    """Generate markdown content from the folder structure."""
    markdown_content = "# S3 Bucket Explorer\n\n"
    
    for main_folder, subfolders in sorted(folder_structure.items()):
        markdown_content += f"## {main_folder}\n\n"
        
        # Handle files in the root of main folder
        if '' in subfolders and subfolders['']:
            for filename, url in sorted(subfolders['']):
                markdown_content += f"- [{filename}]({url})\n"
            markdown_content += "\n"
            
        # Handle subfolders
        for subfolder, files in sorted(subfolders.items()):
            if subfolder != '':
                markdown_content += f"### {subfolder}\n\n"
                for filename, url in sorted(files):
                    markdown_content += f"- [{filename}]({url})\n"
                markdown_content += "\n"
    
    return markdown_content

def main():
    try:
        bucket_name = 'bomberdata'
        s3_client = boto3.client('s3')
        
        # Get all objects in the bucket
        logger.info(f"Fetching objects from bucket: {bucket_name}")
        paginator = s3_client.get_paginator('list_objects_v2')
        objects = []
        
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                objects.extend(page['Contents'])
        
        # Create folder structure
        folder_structure = create_folder_structure(objects)
        
        # Generate markdown content
        markdown_content = generate_markdown(folder_structure)
        
        # Write to file
        output_path = Path('s3_bucket_index.md')
        with open(output_path, 'w') as f:
            f.write(markdown_content)
        
        logger.info(f"Successfully generated index at: {output_path}")
        
    except Exception as e:
        logger.error(f"Error generating index: {e}")
        raise

if __name__ == "__main__":
    main()