import networkx as nx
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import os
from pathlib import Path
import pickle
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

def clean_filename(text):
    """Clean text to create a valid filename"""
    # Remove special characters and limit length
    import re
    # Remove special characters except underscores and hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace spaces with underscores
    text = re.sub(r'\s+', '_', text)
    # Limit length to 50 characters
    text = text[:50]
    return text

def get_embedding(text):
    text = text.replace("\n", " ")
    # print(f"Getting embedding for: {text}...")
    # print(f"Type of text: {type(text)}")
    try:
        response = client.embeddings.create(input=text, model="text-embedding-ada-002")
        if response.data and response.data[0].embedding:
            return np.array(response.data[0].embedding)
        else:
            print("OpenAI API returned an unexpected response structure")
            return None
    except Exception as e:
        print(f"Error when processing text: {text[:50]}...")
        print(f"API returned an error: {e}")
        return None

def get_max_similarity(embedding, statement_embeddings):
    """Calculate maximum cosine similarity between an embedding and a set of statement embeddings"""
    similarities = cosine_similarity(embedding.reshape(1, -1), statement_embeddings)
    return np.max(similarities)

def process_author_chunks(G, realist_statements, moralist_statements):
    """Process chunks for each author and compute similarity scores"""
    
    # Create scores directory if it doesn't exist
    Path("scores").mkdir(exist_ok=True)
    
    print("Grouping nodes by author and title")
    # Group nodes by author and title
    author_groups = {}
    for node, data in G.nodes(data=True):
        if 'author' in data and 'title' in data and 'embedding' in data:
            key = (data['author'], data['title'])
            if key not in author_groups:
                author_groups[key] = []
            author_groups[key].append((node, data['embedding']))
    
    # Get embeddings for statements    
    realist_embeddings = np.array([get_embedding(stmt) for stmt in realist_statements])
    moralist_embeddings = np.array([get_embedding(stmt) for stmt in moralist_statements])
    
    # Process each author's chunks
    for (author, title), nodes_embeddings in author_groups.items():
        print(f"Processing {author} - {title}")
        scores = []
        node_ids = []
        
        # Process each chunk
        for node_id, embedding in nodes_embeddings:
            # Get max similarities
            realist_sim = get_max_similarity(embedding, realist_embeddings)
            moralist_sim = get_max_similarity(embedding, moralist_embeddings)
            
            # Calculate relative score (realist - moralist)
            relative_score = realist_sim - moralist_sim
            
            scores.append(relative_score)
            node_ids.append(node_id)
        
        # Create and save DataFrame
        df = pd.DataFrame({
            'node': node_ids,
            'score': scores
        })
        
        # Create filename from author and title with cleaning
        clean_author = clean_filename(author)
        clean_title = clean_filename(title)
        filename = f"scores/{clean_author}_{clean_title[:30]}.csv"  # Limit title length further
        df.to_csv(filename, index=False)
        
        # Optional: Print summary statistics
        print(f"\nAuthor: {author}")
        print(f"Title: {title}")
        print(f"Number of chunks: {len(scores)}")
        print(f"Average score: {np.mean(scores):.3f}")
        print(f"Score distribution saved to: {filename}")

def main():
    # Load the graph
    print("Loading graph")
    with open("./corpora_graph.gpickle", "rb") as f:
        G = pickle.load(f)
        print("Graph loaded")

        # Realist Statements
        realist_statements = [
            "The theory of precision bombing was impractical in real wartime conditions due to unanticipated operational challenges and complexities, leading to a departure from pre-war strategic bombing doctrines.",
            "Precision bombing was largely ineffective due to technological limitations, with a very low percentage of bombs hitting their intended targets even with advanced equipment.",
            "The belief in unescorted bombers' self-defense capabilities was misguided, leading to significant losses, and daylight precision bombing posed insurmountable challenges in terms of bomber survivability and crew safety.",
            "Precision bombing required unsustainably large numbers of aircraft and prolonged campaigns, making it impractical and ineffective against resilient enemy economies.",
            "The catastrophic losses during the Schweinfurt raids highlighted the failure of precision bombing and the flawed belief in unescorted bombers' ability to defend themselves.",
            "The Schweinfurt raids demonstrated that precision bombing was ineffective and unsustainable due to high attrition rates and inadequate escort capabilities.",
            "The effectiveness of area bombing with incendiary weapons, as demonstrated in attacks like Hamburg, led to its adoption as a more practical and impactful strategy over precision bombing.",
            "Technological advancements and proven effectiveness of incendiary area bombing techniques justified the shift from precision to area bombing strategies.",
            "The shift to area bombing was justified as a response to German initiation of city bombings, setting a precedent for targeting civilian areas.",
            "In total war, the distinction between military and civilian targets disappears, justifying area bombing to pressure the enemy population and government.",
            "Industrial workers contributing to the war effort are legitimate targets, making area bombing of industrial cities a justified military strategy.",
            "Bombing to disrupt industrial capacity and 'dehouse' workers is a legitimate military tactic, and civilian casualties are unfortunate but lawful consequences.",
            "The effectiveness of area bombing in hastening victory justifies its use over less effective methods, prioritizing military success over moral concerns.",
            "Civilian innocence is questionable in total war, and strategic bombing is a necessary evil within the greater evil of war itself.",
            "War naturally escalates to greater brutality; area bombing was an inevitable and justified progression to achieve victory in total war, driven by operational necessity and technological advancements."
        ]

        # Moralist Statements
        moralist_statements = [
            "The supposed distinction between precision and area bombing was misleading; both aimed to terrorize populations, revealing an immoral intent in strategic bombing.",
            "The conduct of U.S. bombing campaigns showed deliberate targeting of cities and civilians, contradicting claims of precision and revealing an immoral strategy.",
            "The shift from precision to indiscriminate bombing was not due to necessity but reflected an immoral strategy aimed at maximum destruction.",
            "Emotional vengeance, not military necessity, motivated strategic bombing, making it an immoral act driven by retribution.",
            "Military leaders became morally detached 'amoral technicians,' facilitating vengeance-driven bombing without ethical consideration.",
            "The pursuit of victory at all costs led to the erosion of moral restraints, resulting in immoral actions like indiscriminate bombing and use of atomic weapons.",
            "Justifying civilian deaths as 'necessary for victory' is morally untenable, as it allows for any atrocity in the name of total victory.",
            "The ethical examination of Allied bombing is hindered by societal reluctance to criticize actions taken during 'the good war,' obscuring immoral conduct.",
            "Total war tactics like area bombing are counterproductive, prolonging conflict and poisoning post-war peace, thus morally unjustifiable.",
            "Even in total war, efforts were made to minimize civilian casualties; thus, the extent of destruction caused by area bombing was unnecessary and immoral.",
            "Governments have moral obligations to enemy civilians; disregarding their rights in favor of protecting one's own soldiers is ethically flawed.",
            "The escalation to area bombing reflects a descent into barbarism, rejecting civilized moral constraints and revealing the inherent immorality of modern warfare.",
            "Strategic bombing represents the inevitable moral decay in warfare, revealing its true barbaric nature when moral pretenses are discarded."
        ]
        
        # Process the chunks
        process_author_chunks(G, realist_statements, moralist_statements)

if __name__ == "__main__":
    main()