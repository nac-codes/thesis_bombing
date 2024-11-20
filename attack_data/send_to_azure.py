import os
import sys
import time
import json
import random
from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.exceptions import HttpResponseError, ServiceRequestError

# Set your endpoint and key from environment variables
endpoint = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
key = os.getenv("AZURE_FORM_RECOGNIZER_KEY")

# Initialize the Document Analysis Client
document_analysis_client = DocumentAnalysisClient(
    endpoint=endpoint, credential=AzureKeyCredential(key)
)

# Define rate limits
RATE_LIMIT_ANALYZE = 5  # Reduced Transactions per second (TPS) for Analyze
DELAY_ANALYZE = 1 / RATE_LIMIT_ANALYZE + 2  # Increased delay per request for Analyze

# Function to analyze a document and save the result as a JSON file
def analyze_document(image_path):
    print(f"Analyzing {image_path}")
    max_retries = 10
    base_delay = 5  # Start with a 5-second delay
    
    for attempt in range(max_retries):
        with open(image_path, "rb") as image_file:
            try:
                poller = document_analysis_client.begin_analyze_document(
                    "prebuilt-layout", document=image_file
                )
                result = poller.result()

                # Construct the output path for the JSON result
                output_path = os.path.splitext(image_path)[0] + ".json"
                
                # Save the result as a JSON file
                with open(output_path, "w") as json_file:
                    json.dump(result.to_dict(), json_file, indent=4)
                
                print(f"Processed and saved result for {image_path} to {output_path}")
                return  # Success, exit the function
            except (HttpResponseError, ServiceRequestError) as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"Error analyzing {image_path}: {str(e)}")
                    print(f"Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                else:
                    print(f"Failed to analyze {image_path} after {max_retries} attempts: {str(e)}")


def process_directory(directory):
    images = []
    for root, _, files in os.walk(directory):
        for f in files:
            if f.lower().endswith('.jpg'):
                image_path = os.path.join(root, f)
                json_path = os.path.splitext(image_path)[0] + ".json"
                if not os.path.exists(json_path):
                    images.append(image_path)

    total_images = len(images)
    print(f"Total images to be processed: {total_images}")
    confirmation = input("Do you want to proceed with processing these images? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("Processing aborted.")
        return

    for image in images:
        analyze_document(image)
        time.sleep(DELAY_ANALYZE)  # Respect rate limit
    
    print("Processing complete.")


if __name__ == "__main__":
    # Run the process_directory function for a given directory
    directory = sys.argv[1]
    
    process_directory(directory)
