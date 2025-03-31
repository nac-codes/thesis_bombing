# APPENDIX 3: Methodology for Sentiment Analysis

This project aims to analyze how American newspapers from the period 1943–1946 used and framed the term “strategic bombing.” Below is a step-by-step explanation of how each script contributed to the data collection, preprocessing, and analysis pipeline. The final result is a time-based classification (e.g., precision, area, industrial, counterforce, countervalue, nuclear, and unrelated/NA) of thousands of newspaper articles, culminating in a visual “market share” graph showing how these categories evolved over time.

---

## 1. Obtaining and Managing Website Cookies

### Script: `get_cookies.py`
The first step requires accessing an online newspaper archive, which usually needs authentication.

1. **What It Does**  
   - Automates the login process to the newspaper archive (newspapers.com in this example) via a Columbia University SSO (Single Sign-On) flow.  
   - Handles Duo two-factor authentication using Selenium.  
   - Saves the user’s authenticated session cookies locally (in `cookies_newspapers.json`) for future reuse.

2. **Why It Matters**  
   - Most archives require login credentials.  
   - Storing cookies allows the main scraping script to bypass the repeated login process.

---

## 2. Scraping Newspaper Articles

### Script: `scrape.py`
Once cookies are acquired, the next step is to actually **scrape** newspaper articles that match the user’s search results.

1. **What It Does**  
   - **Extracts a list of relevant article URLs** from pre-downloaded or saved search results pages (`search_results*.html`).  
   - **Uses Selenium** along with the cookies from `get_cookies.py` to authenticate.  
   - Visits each article’s webpage, collects the HTML source, and extracts:
     - **Page metadata** to store in `info.txt.met` (includes snippet about the article or publication date).  
     - **Article content** (the textual transcript) to store in `content.txt`.
   - Organizes each article by its image ID in a subfolder (e.g., `IMG_12345`).

2. **Why It Matters**  
   - Without scraping, we cannot access or download the text used for analysis.  
   - Each article is encapsulated in its own directory, keeping links between metadata and the corresponding article content.

---

## 3. Parsing Metadata to Structured JSON

### Script: `extract_metadata.py`
After scraping, each folder has an `info.txt.met` file with raw metadata (e.g., date, newspaper name, page). We convert this into a structured JSON file (`info.txt.json`).

1. **What It Does**  
   - Walks through all subfolders looking for `.txt.met` files.  
   - Parses the contained text with a regular expression, extracting:
     - **Publication Date** (day, month, year)  
     - **Newspaper Name**  
     - **Archive Source**  
   - Creates a JSON file (`info.txt.json`) in the same folder, including this structured metadata.

2. **Why It Matters**  
   - Dates and newspaper names are essential for time‐series analysis.  
   - Uniform JSON ensures consistency for the next steps.

---

## 4. Extracting Bombing Snippets

### Script: `extract_snippets.txt`
We only want to analyze passages that mention the keyword *“strategic bombing.”*

1. **What It Does**  
   - Searches each `content.txt` file for the phrase “strategic bombing.”  
   - For each match, captures a specified number of surrounding words (e.g., ±150 words).  
   - Writes that extracted text into a new file called `bombing_snippet.txt`.

2. **Why It Matters**  
   - Many historical newspaper articles contain large amounts of text, and only a portion directly discusses strategic bombing.  
   - By isolating relevant “bombing_snippet.txt,” we focus GPT analysis on the relevant excerpt.

---

## 5. GPT Analysis and Categorization

### Script: `analysis.py`
The preprocessed snippets are then run through an LLM (GPT) to determine which strategic bombing categories they reflect (if any).

1. **What It Does**  
   - Walks through each subfolder to see if `bombing_snippet.txt` is present.  
   - If there is no `gpt_analysis.json`, it sends the snippet to GPT.  
   - The GPT prompt:
     - Asks for a short discussion and tone analysis.  
     - Requests categorization into one or more of:  
       *Precision Bombing, Area Bombing, Industrial Bombing, Counterforce Bombing, Countervalue Bombing, Nuclear Bombing, or Unrelated/NA.*  
   - Saves GPT’s response as `gpt_analysis.json`.

2. **Why It Matters**  
   - Provides consistent, machine‐readable metadata about how the article frames strategic bombing.  
   - Skips folders that already have a `gpt_analysis.json`, allowing crash recovery and incremental updates.

---

## 6. Combining the Data & Visualizing Trends

### Script: `combine_and_plot.py`
Finally, we unite both metadata (`info.txt.json`) and GPT analysis (`gpt_analysis.json`) into a single CSV. Then we visualize how categories evolved across time.

1. **What It Does**  
   **Combining to CSV**  
   - Locates folders that contain both `info.txt.json` and `gpt_analysis.json`.  
   - Extracts:
     - *Date* (from `info.txt.json`).  
     - *Categories* (from `gpt_analysis.json`).  
   - Maps them to standardized columns (Precision, Area, Industrial, Counterforce, Countervalue, Nuclear).  
   - Creates and/or appends to a CSV file (`combined_bombing_data.csv`), one row per article.  

   **Plotting the “Market Share”**  
   - Converts the CSV to a Pandas DataFrame.  
   - Bins articles into time intervals (default: 100 days).  
   - For each time bin, calculates the percentages of articles mentioning each category.  
   - Plots multiple percentage lines on a single graph, illustrating how coverage trends changed over time.

2. **Why It Matters**  
   - Aggregating data across thousands of articles reveals long-term patterns in how newspapers discussed strategic bombing.  
   - The market-share–style plot visually communicates shifts in emphasis from one bombing method to another, or an overall rise in references to destructive tactics.

---

## Overall Workflow

1. **Authentication (get_cookies.py)**  
   Acquire session cookies and handle login.

2. **Scraping Articles (scrape.py)**  
   Loop through each article search result, visit the page (using cookies), download content, and store text files.

3. **Metadata Structuring (extract_metadata.py)**  
   Convert raw `.txt.met` files to structured `info.txt.json` with precise date and newspaper info.

4. **Targeted Snippets (extract_snippets.txt)**  
   Focus on text containing “strategic bombing” by extracting short contexts into `bombing_snippet.txt`.

5. **AI Analysis (analysis.py)**  
   Use GPT to categorize each snippet, writing final results to `gpt_analysis.json`.

6. **Merge & Visualize (combine_and_plot.py)**  
   Combine date + category data into a CSV, then graph category usage over time in 100-day bins.

---

## Conclusion

By following this pipeline, we build a dataset of American newspaper coverage of “strategic bombing” from 1943 to 1946. We see how attentive newspapers were to this specific term and how the framing shifted among discussions of precision, area, industrial, and other bombing types. Ultimately, the data helps illustrate a historical narrative: early emphasis on precision strikes gave way to more extensive coverage of area and countervalue bombing (large-scale attacks on civilian centers) as the war intensified, culminating in a more complex public understanding of strategic bombing’s moral and practical implications.
