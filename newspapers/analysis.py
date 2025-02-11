import os
from pathlib import Path
import json
from openai import OpenAI
import time
from typing import Optional
import concurrent.futures  # Added for parallel processing

class BombingAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.client = OpenAI()
        
    def read_snippet(self, file_path: Path) -> Optional[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return None

    def analyze_snippet(self, snippet: str) -> Optional[dict]:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in strategic bombing ideology. Your job is to analyze the newspaper clippings and categorize the sort of approach to strategic bombing they represent."
                    },
                    {
                        "role": "user",
                        "content": """Find the discussion of strategic bombing in the following newspaper clipping. Discuss what is being said and the tone. Then place the clipping into one or more of the following categories ONLY if the text clearly reflects that specific bombing ideology. If the mention of strategic bombing is unclear, unrelated, or doesn't clearly align with any category, use "Unrelated/NA". Here are the categories:

Precision Bombing: Also known as Pinpoint Bombing. A "surgical" approach aimed at isolating and disabling critical military and industrial nodes. Its intent was to cripple the enemy's war machine with minimal disruption to the broader society, reflecting a belief that a measured, technical strike could reduce the enemy's fighting capacity without directly assaulting the civilian population.

Area Bombing: A strategy born of the total war mindset that deliberately enveloped entire urban centers in massive, indiscriminate bomb loads. More than just a means of destroying factories, area bombing was intended to shatter the morale of the German people by turning cities into symbols of utter devastation—thereby undermining both the economic foundation and the civilian resolve to continue fighting.

Industrial Bombing: An approach focused on dismantling the enemy's "industrial web" by targeting key choke points such as power plants, rail yards, and major factories. The goal was to inflict a cascading collapse on the nation's economic lifeblood, reflecting the idea that in a total war every link in the enemy's production and distribution network was a valid target.

Counterforce Bombing: A tactic designed to strike directly at the enemy's military capability and the installations that supported it. Its intent was to deliver decisive blows that not only reduced combat effectiveness but also signaled that the enemy's organized war potential was vulnerable, thereby sowing doubt and uncertainty among both commanders and troops.

Countervalue Bombing: A more psychologically driven strategy that shifted the focus from just military targets to the heart of the enemy's society. By deliberately attacking civilian population centers and key economic landmarks, this method sought to erode the will to fight—aiming to force the enemy leadership into capitulation by inflicting a profound, demoralizing shock to the very fabric of German society.

Nuclear Bombing: The use of atomic weapons as a means of strategic bombing, representing a quantum leap in destructive capability. This approach combined the physical devastation of area bombing with profound psychological impact, as the sheer scale of destruction and lasting radiation effects created an unprecedented level of deterrence and existential threat.

Unrelated: Use this category when the mention of strategic bombing is incidental, unclear, or doesn't clearly align with any of the above ideologies. This includes cases where strategic bombing is mentioned but the context doesn't reveal a specific strategic approach or philosophical stance.

Important: Only assign a category if the text clearly and explicitly reflects that bombing ideology. If in doubt, use "Unrelated".

Quote: 
{snippet}

Return as JSON:
{{
Discussion: "",
Categories: [ "type of bombing here", "another type here"]
}}"""
                    }
                ],
                response_format={"type": "json_object"},
                temperature=1,
                max_tokens=2048,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"Error in API call: {str(e)}")
            return None

    def process_directory(self, current_dir: Path) -> tuple:
        """
        Process a single directory containing 'bombing_snippet.txt'.
        Returns a tuple (processed, skipped).
        """
        gpt_response_path = current_dir / 'gpt_analysis_2.json'
        
        # Skip if already processed
        if gpt_response_path.exists():
            print(f"Skipped (already exists): {current_dir}")
            return (0, 1)
        
        snippet = self.read_snippet(current_dir / 'bombing_snippet.txt')
        if not snippet:
            print(f"Could not read snippet in: {current_dir}")
            return (0, 0)
        
        print(f"Processing: {current_dir}")
        analysis = self.analyze_snippet(snippet)
        
        if analysis:
            try:
                with open(gpt_response_path, 'w', encoding='utf-8') as f:
                    json.dump(analysis, f, indent=2)
                print(f"Saved analysis to: {gpt_response_path}")
                return (1, 0)
            except Exception as e:
                print(f"Error saving analysis in {current_dir}: {str(e)}")
        return (0, 0)

    def process_directories(self):
        # Gather all directories that have 'bombing_snippet.txt'
        directories = [Path(root) for root, _, files in os.walk(self.root_dir) if 'bombing_snippet.txt' in files]
        total_files = len(directories)
        print(f"Total directories to process: {total_files}")
        
        processed_count = 0
        skipped_count = 0
        max_workers = 5
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Map each directory to a thread pool future
            future_to_dir = {executor.submit(self.process_directory, directory): directory for directory in directories}
            
            completed = 0
            for future in concurrent.futures.as_completed(future_to_dir):
                completed += 1
                try:
                    processed, skipped = future.result()
                    processed_count += processed
                    skipped_count += skipped
                except Exception as e:
                    print(f"Error processing directory {future_to_dir[future]}: {str(e)}")
                print(f"Progress: {completed}/{total_files}")
        
        print(f"\nProcessing complete:")
        print(f"Processed: {processed_count} files")
        print(f"Skipped (already existed): {skipped_count} files")

def main():
    root_dir = '/Users/chim/Working/Thesis/Readings/src/scrape_newspapers/newspaper_articles'
    analyzer = BombingAnalyzer(root_dir)
    analyzer.process_directories()

if __name__ == "__main__":
    main()
