# process_ocr.py

import json
import csv
import sys
import os
import re
import logging
from thefuzz import fuzz
from PIL import Image
from openai import OpenAI


# Get the JPG filename from the JSON filename
json_file = sys.argv[1]

# Configure logging
log_file = '/Users/chim/Working/Thesis/Attack_Images/OCR/PRODUCTION/running/processing_log.txt'

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - [PID %(process)d] - %(levelname)s - %(message)s',
    filemode='a'
)

client = OpenAI()

def process_ocr_data(ocr_data, jpg_file):
    extracted_data = {"metadata": {}, "targets": []}

    expected_column_names = [
        "DATE OF ATTACK DAY", "MO", "YR", "TIME OF ATTACK", "AIR FORCE", "GROUP OR SQUADRON NUMBER",
        "NUMBER OF AIRCRAFT BOMBING", "ALTITUDE OF RELEASE IN HUND. FT.", "SIGHTING",
        "VISIBILITY OF TARGET", "TARGET PRIORITY", "HIGH EXPLOSIVE BOMBS NUMBER",
        "SIZE", "TONS",
        "FUZING NOSE", "TAIL",
        "INCENDIARY BOMBS NUMBER", "SIZE", "TONS",
        "FRAGMENTATION BOMBS NUMBER", "SIZE", "TONS",
        "TOTAL TONS"
    ]
    
    actual_column_names = [
        "DAY", "MONTH", "YEAR", "TIME OF ATTACK", "AIR FORCE", "GROUP/SQUADRON NUMBER",
        "NUMBER OF AIRCRAFT BOMBING", "ALTITUDE OF RELEASE IN HUND. FT.", "SIGHTING",
        "VISIBILITY OF TARGET", "TARGET PRIORITY", "HIGH EXPLOSIVE BOMBS NUMBER",
        "HIGH EXPLOSIVE BOMBS SIZE", "HIGH EXPLOSIVE BOMBS TONS",
        "HIGH EXPLOSIVE BOMBS FUZING NOSE", "HIGH EXPLOSIVE BOMBS FUZING TAIL",
        "INCENDIARY BOMBS NUMBER", "INCENDIARY BOMBS SIZE", "INCENDIARY BOMBS TONS",
        "FRAGMENTATION BOMBS NUMBER", "FRAGMENTATION BOMBS SIZE", "FRAGMENTATION BOMBS TONS",
        "TOTAL TONS"
    ]

    table = find_table_with_23_columns(ocr_data, expected_column_names)
    if not table:
        return None

    table_data = extract_table_data(table, actual_column_names)
    
    extracted_data["table_data"] = table_data

    # Extract target information
    target_info = extract_target_info(ocr_data, jpg_file)
    extracted_data["metadata"] = target_info

    return extracted_data

# def find_orientation_polygons(ocr_data):
#     orientation_keywords = ["TARGET", "LOCATION", "NAME", "LATITUDE", "LONGITUDE", "TARGET CODE"]
#     orientation_polygons = {}

#     # We need to look in pages -> (lines or words or paragraphs)
#     search_space = []
#     for paragraph in ocr_data["paragraphs"]:
#         paragraph["polygon"] = paragraph["bounding_regions"][0]["polygon"]
#         search_space.append(paragraph)

#     # for item in orientation keywords do a fuzzy match on the content of each item, take the max valued item and add it to orientation polygons
#     for keyword in orientation_keywords:
#         logging.info(f"Searching for orientation polygon: {keyword}")
#         max_match_score = 0
#         max_item = None
#         for item in search_space:
#             match_score = fuzz.ratio(keyword, item["content"])
#             if match_score > max_match_score:
#                 max_match_score = match_score
#                 max_item = item
#         if max_item:
#             orientation_polygons[keyword] = max_item["polygon"]
#             logging.info(f"Found orientation polygon: {keyword}")
#     return orientation_polygons

# def calculate_orientation_slope(orientation_polygons):
#     points = []
#     for key in ["TARGET", "LATITUDE", "LONGITUDE", "TARGET CODE"]:
#         if key in orientation_polygons:
#             polygon = orientation_polygons[key]
#             # calculate the center of the polygon
#             center = np.mean([p["x"] for p in polygon]), np.mean([p["y"] for p in polygon])
#             points.append(center)

#     logging.info(f"Points: {points}")
#     x = [p[0] for p in points]
#     y = [p[1] for p in points]
#     slope, _ = np.polyfit(x, y, 1)
#     logging.info(f"Calculated orientation slope: {slope}")
#     return slope

# def extract_target_info(ocr_data, orientation_polygons, orientation_slope, jpg_file):
#     target_info = {}
#     overlap_threshold = 0.1  # 0.5% overlap threshold
#     logging.debug("Starting extraction of target information.")
#     logging.debug(f"Orientation Polygons: {orientation_polygons}")

#     def draw_region(region, jpg_file):
#         # if logging level is DEBUG, draw the region on the image
#         toggle_draw = False
#         if logging.getLogger().getEffectiveLevel() == logging.DEBUG and toggle_draw:
#             img = Image.open(jpg_file)
#             draw = ImageDraw.Draw(img)
#             draw.polygon(region, outline="red")
#             # display the image
#             img.show()

#     def find_text_in_region(region, exclude_polygons=None):
#         best_fit = None
#         best_overlap = 0
#         region_poly = Polygon(region)
#         logging.debug(f"Finding text in region: {region}")
#         for paragraph in ocr_data["paragraphs"]:
#             paragraph_poly = Polygon(to_tuple_list(paragraph["bounding_regions"][0]["polygon"]))
#             logging.debug(f"Checking paragraph: '{paragraph['content']}' with polygon: {paragraph_poly}")
#             if exclude_polygons and any(paragraph_poly.intersects(Polygon(to_tuple_list(poly))) for poly in exclude_polygons):
#                 logging.debug("Excluding paragraph due to intersection with exclude polygons.")
#                 continue
            
#             overlap = polygon_overlap(region_poly, paragraph_poly)
#             logging.debug(f"Overlap with paragraph '{paragraph['content']}': {overlap}")

#             if overlap > best_overlap and overlap > overlap_threshold:
#                 best_overlap = overlap
#                 best_fit = paragraph["content"]
#                 logging.debug(f"New best fit found: {best_fit} with overlap: {best_overlap}")
        
#         return best_fit

#     def polygon_overlap(poly1, poly2):
#         intersection_area = poly1.intersection(poly2).area
#         return intersection_area / poly1.area

#     def calculate_point(x, y, dx, dy):
#         return {
#             'x': x + dx,
#             'y': y + dy + orientation_slope * dx
#         }

#     def to_tuple_list(region):
#         return [(point['x'], point['y']) for point in region]

#     # Extract Target Location
#     if "LOCATION" in orientation_polygons and "TARGET" in orientation_polygons:
#         logging.debug("Extracting Target Location.")
#         location_poly = orientation_polygons["LOCATION"]
#         target_poly = orientation_polygons["TARGET"]
#         logging.debug(f"Location Polygon: {location_poly}, Target Polygon: {target_poly}")
#         target_width = target_poly[1]['x'] - target_poly[0]['x']
#         location_height = location_poly[3]['y'] - location_poly[0]['y']

#         point1 = calculate_point(location_poly[1]['x'], location_poly[1]['y'], 5, 0)
#         point2_x = target_poly[1]['x'] + 3.35 * target_width
#         point2 = {'x': point2_x, 'y': orientation_slope*(point2_x - point1['x']) + location_poly[1]['y']}  
#         point3 = {'x': point2['x'], 'y': point2['y'] + location_height}
#         point4 = location_poly[2]

#         region = to_tuple_list([point1, point2, point3, point4])
#         logging.debug(f"Region for Target Location: {region}")

#         # draw the region on the image
#         draw_region(region, jpg_file)

#         target_info["Target Location"] = find_text_in_region(region, exclude_polygons=orientation_polygons.values())
#         logging.info(f"Extracted Target Location: {target_info['Target Location']}")

#     # Extract Target Name
#     if "NAME" in orientation_polygons and "TARGET" in orientation_polygons:
#         logging.debug("Extracting Target Name.")
#         name_poly = orientation_polygons["NAME"]
#         target_poly = orientation_polygons["TARGET"]
#         logging.debug(f"Name Polygon: {name_poly}, Target Polygon: {target_poly}")
#         target_width = target_poly[1]['x'] - target_poly[0]['x']
#         name_height = name_poly[3]['y'] - name_poly[0]['y']

#         point1 = calculate_point(name_poly[1]['x'], name_poly[1]['y'], 5, 0)
#         point2_x = target_poly[1]['x'] + 3.35 * target_width
#         point2 = {'x': point2_x, 'y': orientation_slope*(point2_x - point1['x']) + name_poly[1]['y']}  
#         point3 = {'x': point2['x'], 'y': point2['y'] + 2 * name_height}
#         point4 = {'x': name_poly[2]['x'], 'y': name_poly[2]['y'] + name_height}

#         region = to_tuple_list([point1, point2, point3, point4])
#         logging.debug(f"Region for Target Name: {region}")

#         # draw the region on the image
#         draw_region(region, jpg_file)

#         target_info["Target Name"] = find_text_in_region(region, exclude_polygons=orientation_polygons.values())
#         logging.info(f"Extracted Target Name: {target_info['Target Name']}")

#     # Extract Latitude
#     if "LATITUDE" in orientation_polygons:
#         logging.debug("Extracting Latitude.")
#         latitude_poly = orientation_polygons["LATITUDE"]
#         logging.debug(f"Latitude Polygon: {latitude_poly}")
#         latitude_height = latitude_poly[3]['y'] - latitude_poly[0]['y']

#         point1 = latitude_poly[3]
#         point2 = latitude_poly[2]
#         point3 = {'x': point2['x'], 'y': point2['y'] + 4 * latitude_height}
#         point4 = {'x': point1['x'], 'y': point1['y'] + 4 * latitude_height}

#         region = to_tuple_list([point1, point2, point3, point4])
#         logging.debug(f"Region for Latitude: {region}")

#         # draw the region on the image
#         draw_region(region, jpg_file)

#         target_info["Latitude"] = find_text_in_region(region, exclude_polygons=orientation_polygons.values())
#         logging.info(f"Extracted Latitude: {target_info['Latitude']}")

#     # Extract Longitude
#     if "LONGITUDE" in orientation_polygons:
#         logging.debug("Extracting Longitude.")
#         longitude_poly = orientation_polygons["LONGITUDE"]
#         logging.debug(f"Longitude Polygon: {longitude_poly}")
#         longitude_height = longitude_poly[3]['y'] - longitude_poly[0]['y']

#         point1 = longitude_poly[3]
#         point2 = longitude_poly[2]
#         point3 = {'x': point2['x'], 'y': point2['y'] + 4 * longitude_height}
#         point4 = {'x': point1['x'], 'y': point1['y'] + 4 * longitude_height}

#         region = to_tuple_list([point1, point2, point3, point4])
#         logging.debug(f"Region for Longitude: {region}")

#         # draw the region on the image
#         draw_region(region, jpg_file)

#         target_info["Longitude"] = find_text_in_region(region, exclude_polygons=orientation_polygons.values())
#         logging.info(f"Extracted Longitude: {target_info['Longitude']}")

#     # Extract Target Code
#     if "TARGET CODE" in orientation_polygons:
#         logging.debug("Extracting Target Code.")
#         target_code_poly = orientation_polygons["TARGET CODE"]
#         logging.debug(f"Target Code Polygon: {target_code_poly}")
#         target_code_height = target_code_poly[3]['y'] - target_code_poly[0]['y']

#         point1 = target_code_poly[3]
#         point2 = target_code_poly[2]
#         point3 = {'x': point2['x'], 'y': point2['y'] + 4 * target_code_height}
#         point4 = {'x': point1['x'], 'y': point1['y'] + 4 * target_code_height}

#         region = to_tuple_list([point1, point2, point3, point4])
#         logging.debug(f"Region for Target Code: {region}")

#         # draw the region on the image
#         draw_region(region, jpg_file)

#         target_info["Target Code"] = find_text_in_region(region, exclude_polygons=orientation_polygons.values())
#         logging.info(f"Extracted Target Code: {target_info['Target Code']}")

#     logging.debug("Finished extraction of target information.")
#     return target_info

def send_to_ai(prompt, attributes, max_retries=3, model="gpt-4o"):
    for attempt in range(max_retries):
        try:
            # Append instructions for JSON format
            attributes_str = ", ".join([f'"{attr}"' for attr in attributes])
            full_prompt = f"{prompt}\n\nPlease return the extracted values for {attributes_str} in the following JSON format:\n```json\n{{\n"
            for attr in attributes:
                full_prompt += f'  "{attr}": "extracted_value_here",\n'
            full_prompt = full_prompt.rstrip(',\n') + "\n}\n```"
            
            logging.info(f"Attempt {attempt + 1}: Sending prompt to AI:\n{full_prompt}")

            # Make the API call
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts target information from US Strategic Bombing Survey documents."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.3,
                top_p=0.5
            )
            
            # Extract the JSON part from the response
            full_response = response.choices[0].message.content.strip()
            logging.info(f"Received full response from AI:\n{full_response}")

            # Use regex to find the JSON part
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', full_response)
            if json_match:
                json_str = json_match.group(1)
                logging.info(f"Extracted JSON from response:\n{json_str}")
            else:
                logging.warning("No JSON found in the response. Retrying...")
                continue

            # Parse the JSON
            result = json.loads(json_str)
            
            # Check if all expected attributes are in the result
            if all(attr in result for attr in attributes):
                logging.info(f"Successfully received all expected attributes: {result}")
                return result
            else:
                logging.warning(f"Attempt {attempt + 1}: JSON response does not contain all expected attributes. Retrying...")
        except json.JSONDecodeError:
            logging.error(f"Attempt {attempt + 1}: Failed to parse JSON. Retrying...")
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}: An error occurred: {str(e)}. Retrying...")
    
    logging.error(f"Failed to get a valid response after {max_retries} attempts.")
    return None

def extract_target_info(ocr_data, jpg_file):
    logging.debug("Starting extraction of target information.")

    image_height = 4000
    # Load the image to get its height
    with Image.open(jpg_file) as img:
        image_height = img.height
    
    top_third_paragraphs = [p['content'] for p in ocr_data['paragraphs'] if p['bounding_regions'][0]['polygon'][2]['y'] <= image_height / 3]
    
    # Concatenate the paragraphs
    context = "\n".join(top_third_paragraphs)

    # Prepare the prompt
    prompt = f"""
    Extract the following information from the given text:
    
    1. Target Location: The city or area where the target is located.
    2. Target Name: The specific name of the target, often including a company or facility name.
    3. Latitude: The latitude coordinate, usually in the format of degrees and minutes (e.g., 5223N for 52°23'N).
    4. Longitude: The longitude coordinate, usually in the format of degrees and minutes (e.g., 944E for 9°44'E).
    5. Target Code: A numeric or alphanumeric code identifying the target, often in the format of 5-6 digits followed by 3 digits.

    Here's the text to extract from:

    {context}

    Please provide the most likely values for each field based on the given information. Return NA as a value if there is no possible corresponding value.
    """

    attributes = ["Target Location", "Target Name", "Latitude", "Longitude", "Target Code"]
    
    result = send_to_ai(prompt, attributes)
    
    if result:
        logging.info("Successfully extracted target information.")
        return result
    else:
        logging.error("Failed to extract target information.")
        return {attr: "" for attr in attributes}


def find_table_with_23_columns(ocr_data, expected_column_names):
    if "tables" not in ocr_data or len(ocr_data["tables"]) == 0:
        logging.warning("No tables found in OCR data")
        return None
    
    best_match_score = 0
    best_match_table = None
    best_match_start = None

    for table in ocr_data["tables"]:
        logging.info(f"Examining table with {table['column_count']} columns")
        
        if table['column_count'] < 23:
            logging.info(f"Skipping table with fewer than 23 columns")
            continue

        column_headers = [[] for _ in range(table['column_count'])]
        for cell in table['cells']:
            if cell['kind'] == 'columnHeader':
                column_headers[cell['column_index']].append(cell['content'])

        column_names = [' '.join(headers) for headers in column_headers]
        logging.debug(f"Full list of column names: {column_names}")

        for start in range(table['column_count'] - 22):
            selected_columns = column_names[start:start+23]
            logging.debug(f"Examining columns starting at index {start}")
            logging.debug(f"Selected column names: {selected_columns}")

            total_score = 0
            for expected, actual in zip(expected_column_names, selected_columns):
                if expected.lower() in actual.lower():
                    score = 100  # Give full score if expected is contained in actual
                else:
                    score = fuzz.ratio(expected, actual)
                total_score += score

            avg_score = total_score / 23

            logging.info(f"Average match score for columns starting at index {start}: {avg_score}")

            if avg_score > best_match_score:
                best_match_score = avg_score
                best_match_table = table
                best_match_start = start
                logging.info(f"New best match found with score {best_match_score}")

    if best_match_table:
        logging.info(f"Best matching table found with score {best_match_score}")
        logging.info(f"Selected columns start at index: {best_match_start}")
        
        # Filter the cells to include only the best matching columns
        best_match_table['cells'] = [
            cell for cell in best_match_table['cells'] 
            if best_match_start <= cell['column_index'] < best_match_start + 23
        ]
        
        # Update the column count
        best_match_table['column_count'] = 23
        
        # Adjust column indices
        for cell in best_match_table['cells']:
            cell['column_index'] -= best_match_start
        
        return best_match_table
    else:
        logging.warning("No suitable table found")
        return None

def extract_table_data(table, expected_names):
    data = {name: [""] * table["row_count"] for name in expected_names}
    for cell in table["cells"]:
        if cell["kind"] == "content":
            column_index = cell["column_index"]
            if column_index < len(expected_names):
                name = expected_names[column_index]
                row_index = cell["row_index"]
                if row_index < len(data[name]):
                    data[name][row_index] = cell["content"].strip()
    
    logging.debug(f"Extracted table data: {data}")
    return data

def save_csv(data, filename):
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(data.keys())
        writer.writerows(zip(*data.values()))

def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# Main execution
if __name__ == "__main__":
    file = sys.argv[1]
    with open(file, 'r') as f:
        ocr_data = json.load(f)

    # find the corresponding JPG image file
    jpg_file = file.replace(".json", ".JPG")
    if not os.path.exists(jpg_file):
        logging.error(f"Corresponding JPG file not found: {jpg_file}")
        exit(1)
    
    logging.info(f"--------------Processing {jpg_file}--------------")

    # create an output folder from the name of the file in the same directory as the file. 
    output_path = file.replace(".json", "_output")
    os.makedirs(output_path, exist_ok=True)

    extracted_data = process_ocr_data(ocr_data, jpg_file)        
    if extracted_data is None:
        logging.error("No suitable table found in the OCR data. Exiting.")
        exit(0)

    save_json(extracted_data, output_path + "/extracted_data.json")
    save_csv(extracted_data["table_data"], output_path + "/table_data.csv")
    logging.info("Data extraction complete. Check extracted_data.json and table_data.csv for results.")
