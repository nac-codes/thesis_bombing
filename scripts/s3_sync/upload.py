import os
import boto3
import logging
from pathlib import Path
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def upload_file_to_s3(local_path, bucket_name, s3_key):
    """Upload a single file to S3."""
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(str(local_path), bucket_name, s3_key)
        logger.info(f"Successfully uploaded: {s3_key}")
    except ClientError as e:
        logger.error(f"AWS error uploading {local_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error uploading {local_path}: {e}")
        return False
    return True

def process_archive_and_attack_images(base_path, bucket_name):
    """Process Archive and Attack_Images directories for JPG files."""
    if not base_path.exists():
        logger.error(f"Directory not found: {base_path}")
        return

    try:
        files_processed = 0
        for root, _, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith('.jpg'):
                    try:
                        local_path = Path(root) / file
                        relative_path = local_path.relative_to(base_path.parent.parent)
                        s3_key = str(relative_path).replace('Thesis/', '', 1)
                        if upload_file_to_s3(local_path, bucket_name, s3_key):
                            files_processed += 1
                    except ValueError as e:
                        logger.error(f"Path error processing {file}: {e}")
                        continue
        logger.info(f"Processed {files_processed} images from {base_path}")
    except Exception as e:
        logger.error(f"Error processing directory {base_path}: {e}")

def process_readings(readings_path, bucket_name):
    """Process Readings directory for chunks and .met files."""
    if not readings_path.exists():
        logger.error(f"Readings directory not found: {readings_path}")
        return

    corpora_path = readings_path / 'corpora'
    if not corpora_path.exists():
        logger.error(f"Corpora directory not found: {corpora_path}")
        return

    try:
        files_processed = 0
        for corpus_dir in corpora_path.iterdir():
            if not corpus_dir.is_dir():
                continue

            # Upload all txt files from chunks directory
            chunks_dir = corpus_dir / 'chunks'
            if chunks_dir.exists():
                try:
                    for txt_file in chunks_dir.glob('*.txt'):
                        try:
                            relative_path = txt_file.relative_to(readings_path.parent.parent)
                            s3_key = str(relative_path).replace('Thesis/', '', 1)
                            if upload_file_to_s3(txt_file, bucket_name, s3_key):
                                files_processed += 1
                        except ValueError as e:
                            logger.error(f"Path error processing {txt_file}: {e}")
                            continue
                except Exception as e:
                    logger.error(f"Error processing chunks directory {chunks_dir}: {e}")
                    continue

            # Upload .met file if it exists
            met_file = corpus_dir / f"{corpus_dir.name}.txt.met"
            if met_file.exists():
                try:
                    relative_path = met_file.relative_to(readings_path.parent.parent)
                    s3_key = str(relative_path).replace('Thesis/', '', 1)
                    if upload_file_to_s3(met_file, bucket_name, s3_key):
                        files_processed += 1
                except ValueError as e:
                    logger.error(f"Path error processing {met_file}: {e}")

        logger.info(f"Processed {files_processed} files from Readings directory")
    except Exception as e:
        logger.error(f"Error processing Readings directory: {e}")

def main():
    try:
        bucket_name = 'bomberdata'
        base_path = Path('/Users/chim/Working/Thesis')
        
        if not base_path.exists():
            logger.error(f"Base directory not found: {base_path}")
            return

        # Process Archive directory
        archive_path = base_path / 'Archive'
        if archive_path.exists():
            process_archive_and_attack_images(archive_path, bucket_name)
        else:
            logger.warning(f"Archive directory not found: {archive_path}")

        # Process Attack_Images directory
        attack_images_path = base_path / 'Attack_Images' / 'BOXES'
        if attack_images_path.exists():
            process_archive_and_attack_images(attack_images_path, bucket_name)
        else:
            logger.warning(f"Attack_Images directory not found: {attack_images_path}")

        # Process Readings directory
        readings_path = base_path / 'Readings'
        if readings_path.exists():
            process_readings(readings_path, bucket_name)
        else:
            logger.warning(f"Readings directory not found: {readings_path}")

    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise

if __name__ == "__main__":
    main()