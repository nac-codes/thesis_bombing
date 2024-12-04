import pandas as pd
import networkx as nx
import pickle
import os
from pathlib import Path

# Base paths
base_dir = '/Users/chim/Working/Thesis/Production/scripts/literature_review'
scores_dir = os.path.join(base_dir, 'scores')
output_dir = os.path.join(scores_dir, 'analysis')

# Create output directory if it doesn't exist
Path(output_dir).mkdir(parents=True, exist_ok=True)

# Load the graph
gpickle_file = os.path.join(base_dir, 'corpora_graph.gpickle')
with open(gpickle_file, 'rb') as f:
    G = pickle.load(f)

# Function to get content for nodes
def get_node_content(nodes):
    content = []
    for _, row in nodes.iterrows():
        node_id = row['node']
        try:
            node_data = G.nodes[int(node_id)]
            content.append(f"Node: {node_id}, Score: {row['score']}, Chunk File: {node_data.get('chunk_file', 'No file available')}, Content: {node_data.get('content', 'No content available')}")
        except KeyError:
            print(f"Node {node_id} not found in the graph.")
    return content

# Process each CSV file in the scores directory
for csv_file in Path(scores_dir).glob('*.csv'):
    # Skip if it's in the analysis subdirectory
    if 'analysis' in str(csv_file):
        continue
        
    print(f"Processing {csv_file.name}...")
    
    # Create output filenames
    base_name = csv_file.stem
    positive_output_file = os.path.join(output_dir, f'{base_name}_top_positive_nodes.txt')
    negative_output_file = os.path.join(output_dir, f'{base_name}_top_negative_nodes.txt')
    
    # Load and process the CSV file
    df = pd.read_csv(csv_file, sep=',', header=None, names=['node', 'score'])
    df['score'] = pd.to_numeric(df['score'], errors='coerce')
    df = df.dropna(subset=['score'])
    
    # Get top 20 most positive and most negative nodes
    top_positive = df.nlargest(20, 'score')
    top_negative = df.nsmallest(20, 'score')
    
    # Get content for top positive and negative nodes
    positive_content = get_node_content(top_positive)
    negative_content = get_node_content(top_negative)
    
    # Save to text files
    with open(positive_output_file, 'w') as f:
        f.write("\n".join(positive_content))
    
    with open(negative_output_file, 'w') as f:
        f.write("\n".join(negative_content))

print("All files processed. Results saved in scores/analysis/")