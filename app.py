from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_session import Session  # Add this import
import pandas as pd
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time
from googleapiclient.errors import HttpError
import redis
from serpapi.google_search import GoogleSearch
from utils import parse_web_results, fetch_and_store_content, extract_information_with_llm
import csv
import re
from flask import Response
from flask import send_file
from groq import Groq

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './uploads'

# Path to your Google API credentials JSON file
#GOOGLE_CLIENT_SECRETS_FILE = "client_secretid.json"
SCOPES = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/spreadsheets.readonly']

HEET_ID = None
RANGE = 'Sheet1!A1:Z100'

# Use Redis for session storage
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_COOKIE_NAME'] = 'your_session_cookie'
app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6380, db=0)  # Adjust Redis config as necessary
Session(app)  # Initialize session

app.secret_key = 'your_flask_secret_key'  # Replace with a secure key for session management

# Load the API keys from the JSON file
with open("api_keys.json", "r") as file:
    api_keys = json.load(file)

# Access the keys
serpapi_key = api_keys["serpapi"]
groqapi_key = api_keys["groqapi"]
webscrapingapi_key = api_keys["webscrapingapi"]


# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Google Sheets API configuration
SERVICE_ACCOUNT_FILE = './credentials.json'  # Path to your Google credentials file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Function to read data from a Google Sheet
def read_google_sheet(spreadsheet_id, range_name, retries=3, delay=5):
    service = build('sheets', 'v4', credentials=credentials)
    sheet = service.spreadsheets()

    for attempt in range(retries):
        try:
            result = sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
            return result.get('values', [])
        except HttpError as e:
            if e.resp.status == 503:
                print(f"Service unavailable (attempt {attempt + 1}). Retrying after {delay} seconds...")
                time.sleep(delay)
            else:
                raise e

    raise Exception("Failed to access Google Sheets after multiple attempts.")

def search_web(entity):
    """Perform a web search using SerpAPI for a given entity."""
    params = {
        "engine": "google",
        "q": entity,
        "api_key": serpapi_key
    }
    search = GoogleSearch(params)
    results = search.get_dict()

    # Check if results is actually a dictionary
    if isinstance(results, dict):
        # Return relevant results (e.g., URLs and snippets)
        return results.get('organic_results', [])[:5]  # Limit to 5 results for efficiency
    else:
        # Log or print an error if the results are not in the expected format
        print("Unexpected response format:", results)
        return []


def extract_sheet_id(url):
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if match:
        return match.group(1)
    else:
        flash('Invalid Google Sheets URL.')
        return None



def get_google_sheets_service():
    """
    Authenticate using service account credentials and return the Sheets service.
    """
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
    service = build('sheets', 'v4', credentials=credentials)
    return service

def fetch_sheet_data(sheet_id):
    """
    Fetch data from the Google Sheet using its sheet ID.
    """
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        
        # Fetch data from range (adjust as needed for your sheet)
        result = sheet.values().get(spreadsheetId=sheet_id, range='Sheet1!A1:Z100').execute()
        values = result.get('values', [])

        if not values:
            flash('No data found in the selected Google Sheet.')
            return None

        # Convert the Google Sheet data to a DataFrame (assuming the first row is the header)
        df = pd.DataFrame(values[1:], columns=values[0])  
        return df.to_html()  # Return HTML table representation for displaying in the template
    except Exception as e:
        flash(f"An error occurred while fetching the Google Sheet: {e}")
        return None


@app.route('/', methods=['GET', 'POST'])
def home():
    sheet_data = None
    csv_data = None

    if request.method == 'POST':
        # Handle CSV upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            if file:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                # Preview data (first 5 rows)
                df = pd.read_csv(filepath)
                # Save DataFrame to session for future use in query generation
                session['uploaded_data'] = df.to_dict()  # Save as dictionary format for session

                preview_data = df.head().to_html()  # Convert DataFrame to HTML for display
                csv_data = preview_data  # Save CSV preview to be displayed
                sheet_data = None  # Clear Google Sheets data if CSV is uploaded

        # Handle Google Sheets URL input
        elif 'google_sheet_url' in request.form:
            sheet_url = request.form['google_sheet_url']
            sheet_id = extract_sheet_id(sheet_url)
            if sheet_id:
                sheet_data = fetch_sheet_data(sheet_id)
                csv_data = None  # Clear CSV data if Google Sheets URL is provided

    return render_template('index.html', sheet_data=sheet_data, csv_data=csv_data)



@app.route('/process_query', methods=['POST'])
def process_query():
    # Retrieve the uploaded data from session (if available)
    uploaded_data_dict = session.get('uploaded_data', {})
    if not uploaded_data_dict:
        flash('No CSV data available to generate queries.')
        return redirect(url_for('home'))

    uploaded_data = pd.DataFrame(uploaded_data_dict)

    if request.method == 'POST':
        custom_prompt = request.form['custom_prompt']
        search_queries = []

        for _, row in uploaded_data.iterrows():
            processed_prompt = custom_prompt

            for column_name in uploaded_data.columns:
                placeholder = f'{{{column_name}}}'  # Placeholder for dynamic replacement
                if placeholder in processed_prompt:
                    processed_prompt = processed_prompt.replace(placeholder, str(row[column_name]))

            search_queries.append(processed_prompt)

        # Save the generated queries to Redis (store it as a list)
        redis_db = redis.StrictRedis(host='localhost', port=6380, db=0)
        redis_db.set('generated_queries', json.dumps(search_queries))  # Store queries as JSON string

        # Render the queries.html template with the generated queries
        return render_template('queries.html', queries=search_queries)

@app.route('/check_stored_queries', methods=['GET'])
def check_stored_queries():
    redis_db = redis.StrictRedis(host='localhost', port=6380, db=0)
    stored_queries = redis_db.get('generated_queries')
    
    if stored_queries:
        stored_queries = json.loads(stored_queries)  # Convert the stored JSON string back to a Python list
        return render_template('queries.html', queries=stored_queries)
    else:
        return "No queries stored yet."

@app.route('/web_search', methods=['POST'])
def web_search():
    redis_db = redis.StrictRedis(host='localhost', port=6380, db=0)
    stored_queries = redis_db.get('generated_queries')

    if not stored_queries:
        flash('No queries available for web search.')
        return redirect(url_for('home'))

    queries = json.loads(stored_queries)
    search_results = {}

    for query in queries:
        try:
            # Print the query being processed (for debugging purposes)
            print(f"Searching for: {query}")
            results = search_web(query)
            search_results[query] = results
            time.sleep(2)  # Add delay to avoid API rate limiting
        except Exception as e:
            print(f"Error during web search for query '{query}': {e}")
            continue

    # Store the search results in Redis
    redis_db.set('search_results', json.dumps(search_results))
    print("Search results stored in Redis.")

    # Render the results in a template or log them as needed
    return render_template('search_results.html', results=search_results)

# Set up Redis connection
redis_db = redis.StrictRedis(host='localhost', port=6380, db=0)

@app.route('/extract_info', methods=['POST'])
def extract_info():
    # Retrieve search results from Redis
    stored_results = redis_db.get('search_results')
    
    if not stored_results:
        flash('No search results available for information extraction.')
        return redirect(url_for('home'))

    try:
        # Ensure that stored_results is a dictionary (it may be a JSON string, so parse it)
        search_results = json.loads(stored_results)
    except json.JSONDecodeError:
        flash('Error decoding search results from Redis.')
        return redirect(url_for('home'))

    extraction_results = []

    def is_relevant_response(response_text):
        irrelevant_keywords = [
            "does not mention", "referring to a different region",
            "not available", "irrelevant to", "no information on"
        ]
        # Return True only if none of the irrelevant keywords are found in the response text
        return not any(keyword in response_text.lower() for keyword in irrelevant_keywords)

    # Loop over each query and its results in search_results
    for query, results in search_results.items():
        print(f"Processing query: {query}")  # Debug print for query

        # Iterate through each result for the current query
        for item in results:
            # Ensure the item is a dictionary with expected keys
            if isinstance(item, dict):
                url = item.get('link')
                snippet = item.get('snippet', '')

                if url:
                    # Fetch content from the URL and store it in Redis
                    content = fetch_and_store_content(url, api_key=webscrapingapi_key)
                    # Use LLM to extract relevant information from the content
                    extracted_info = extract_information_with_llm(
                        url, 
                        snippet, 
                        query, 
                    )

                    if is_relevant_response(extracted_info):
                        extraction_results.append({
                            'query': query,
                            'url': url,
                            'extracted_info': extracted_info
                        })


    # Store the extraction results in Redis for later retrieval or display
    redis_db.set('extraction_results', json.dumps(extraction_results))
    print("Extraction results stored in Redis.")

    # Render or return results as needed
    return render_template('extraction_results.html', results=extraction_results)



@app.route('/process_extracted_info_json', methods=['GET', 'POST'])
def process_extracted_info_json():
    # Retrieve extraction results from Redis (from the previous step)
    stored_extraction_results = redis_db.get('extraction_results')

    if not stored_extraction_results:
        flash('No extraction results available for processing.')
        return redirect(url_for('home'))

    try:
        # Parse the JSON string of extraction results
        extraction_results = json.loads(stored_extraction_results)
    except json.JSONDecodeError:
        flash('Error decoding extraction results from Redis.')
        return redirect(url_for('home'))

    # Step 1: Initialize a set to keep track of processed queries
    processed_queries = set()  # To track queries that have been processed
    processed_data = []

    # Step 2: Loop through each query in the extraction results and process it one by one
    for result in extraction_results:
        query = result.get('query')
        extracted_info = result.get('extracted_info', "")

        # If this query has already been processed, skip it
        if query in processed_queries:
            continue

        # Mark this query as processed
        processed_queries.add(query)

        # Combine all extracted info for the current query
        combined_extracted_info = []
        for extraction in extraction_results:
            if extraction['query'] == query:
                combined_extracted_info.append(extraction['extracted_info'])

        # Create a refined prompt to extract key-value pairs for the current query
        prompt_template = """
        The task is to process extracted information from a single query. You are given the query and all extracted information related to it.
        Your task is to generate **key-value pairs** based on the query and the extracted data.

        For each query:
        1. Key: Decide the keys solely based on the query. The keys should be minimal in number and cluster similar information into the fewest possible, most meaningful keys (e.g., "Salary" instead of multiple variations like "Annual Salary" or "Pay").**Don't make keys that are not specifically asked in query**.
        2. Value: Use the extracted information to determine the most accurate or appropriate value corresponding to the key. Adjust values based on the context of the key and real worls logic, and if multiple values are provided, combine or calculate the best representation (e.g., use the mean for ranges, or pick the most plausible value).

        Here is the query and all its extracted information:
        Query: {query}
        Don't see the exttracted_info until you have decided the key.
        Extracted Info: {extracted_info}

        Please provide only the key-value pairs in the following format:
        - "<Key>: <Value>"
        Each key-value pair should be on a new line, and there should be no extra words or explanations.

        """

        # Combine all extracted info into one string
        extracted_info_combined = "\n".join(combined_extracted_info)

        prompt = prompt_template.format(query=query, extracted_info=extracted_info_combined)
        client = Groq(api_key=groqapi_key)

        # Call LLM to generate the key-value pairs for the current query
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        # Parse the response to get key-value pairs
        unified_info = response.choices[0].message.content.strip().split("\n")
        key_value_pairs = {}

        for item in unified_info:
            if ":" in item:
                key, value = item.split(":", 1)
                key = key.strip()
                value = value.strip()
                key_value_pairs[key] = value

        print(f"DEBUG: Key-Value Pairs for Query '{query}': {key_value_pairs}")

        # Step 3: Store the processed query data (including key-value pairs)
        processed_data.append({
            "query": query,
            "extracted_info": key_value_pairs  # Store the key-value pairs
        })

    # Step 4: Store the processed data in Redis
    redis_db.set('processed_json_data', json.dumps(processed_data))
    print("DEBUG: Processed JSON data stored in Redis.")

    # Step 5: Render the processed data on the page (showing query and extracted info in key-value pairs)
    return render_template('processed_info_json_page.html', results=processed_data)


@app.route('/processed_labels_page', methods=['GET', 'POST'])
def processed_labels_page():
    # Retrieve the processed JSON data from Redis
    stored_processed_data = redis_db.get('processed_json_data')
    if not stored_processed_data:
        flash('No processed data available for display.')
        return redirect(url_for('home'))

    try:
        processed_data = json.loads(stored_processed_data)
    except json.JSONDecodeError:
        flash('Error decoding processed data from Redis.')
        return redirect(url_for('home'))

    # Step 1: Prepare the output data for LLM processing
    client = Groq(api_key=groqapi_key)

    # Combine all extracted information into a single prompt
    combined_extracted_info = []
    for result in processed_data:
        query = result.get('query')
        extracted_info = result.get('extracted_info', {})
        formatted_extracted_info = f"Query: {query}\nExtracted Info:\n" + "\n".join(
            [f'"{key}": {value}' for key, value in extracted_info.items()]
        )
        combined_extracted_info.append(formatted_extracted_info)

    # Combine all the extracted info into a single input
    all_extracted_info = "\n\n".join(combined_extracted_info)

    # Use the combined data in the LLM prompt
    prompt_template = """
    You are given a query and the extracted information related to it. Your task is to provide only the key-value pairs in the following format:
    Query: Key: Value

    Instructions:  
    1. Key Formation:  
    - Make as few keys as possible. For example, if salary is asked in queries, use only one key ("Salary") and adjust the values of similar items to match the unit.  
    - Form the densest possible cluster of keys. Do the clustering based on real-world logic. If a key is not present in more than 50% of rows, you can remove it.  
    - Create keys based on the extracted information by choosing the most recurring key(s) when multiple related items are mentioned.  

    2. Value Adjustment:  
    - Adjust values using real-world logic (e.g., infer missing units, calculate means for ranges, and ensure consistency across all rows).  
    - If a value cannot be logically inferred, write "Not Mentioned".  

    3. Output Format:  
    - Output each key-value pair on a new line in the format:
      Query: Key: Value

    Input:  
    {extracted_info}

    After the output is decided, check it and if for any key more than half rows it is not mentioned, then delete all those key-value pairs. This is a very important feature.
    Ensure that all values are in logically consistent units.
    """

    # Pass the combined extracted info to the LLM
    prompt = prompt_template.format(extracted_info=all_extracted_info)

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5000
    )

    # Retrieve and clean the LLM output
    llm_output = response.choices[0].message.content.strip()
    cleaned_llm_output = [line.strip() for line in llm_output.splitlines() if line.strip() != ""]

    # Step 2: Process LLM output into table format
    final_data = []
    columns = set()
    for line in cleaned_llm_output:
        parts = line.split(":")
        if len(parts) < 3:
            continue  # Skip malformed lines
        query, key, value = parts[0].strip(), parts[1].strip(), parts[2].strip()
        entry = next((row for row in final_data if row['Query'] == query), None)
        if not entry:
            entry = {"Query": query}
            final_data.append(entry)
        entry[key] = value
        columns.add(key)

    # Step 3: Store the final processed data
    redis_db.set('final_processed_data', json.dumps(final_data))
    print("DEBUG: Final processed data stored in Redis.")

    # Step 4: Render the processed data in a table on the next page
    return render_template('processed_labels_page.html', results=final_data, columns=list(columns))


import csv
import io
from flask import Response

@app.route('/download_final_processed_csv', methods=['GET'])
def download_final_processed_csv():
    # Retrieve the processed data stored in Redis
    stored_processed_data = redis_db.get('final_processed_data')
    if not stored_processed_data:
        flash('No processed data available for download.')
        return redirect(url_for('home'))

    try:
        table_data = json.loads(stored_processed_data)
    except json.JSONDecodeError:
        flash('Error decoding processed data from Redis.')
        return redirect(url_for('home'))

    # Prepare the CSV data
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=table_data[0].keys())
    writer.writeheader()
    for row in table_data:
        writer.writerow(row)
    
    # Seek to the beginning of the StringIO object before sending it
    output.seek(0)

    # Return the CSV as a downloadable file
    return Response(output.getvalue(),
                    mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=final_processed_data.csv"})



@app.route('/download_processed_csv')
def download_processed_csv():
    # Retrieve the processed data from Redis
    processed_data = json.loads(redis_db.get('processed_json_data'))
    
    # Create a CSV response
    def generate_csv():
        # Create CSV writer
        output = csv.DictWriter(
            fieldnames=processed_data[0].keys(),
            delimiter=',',
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL
        )
        output.writeheader()
        for row in processed_data:
            output.writerow(row)
    
    return Response(generate_csv(), 
                    mimetype='text/csv', 
                    headers={'Content-Disposition': 'attachment;filename=processed_data.csv'})


@app.route('/download_csv')
def download_csv():
    # Retrieve extraction results from Redis
    stored_results = redis_db.get('extraction_results')
    if not stored_results:
        flash('No extraction results available to download.')
        return redirect(url_for('home'))
    
    extraction_results = json.loads(stored_results)
    
    # Define the CSV file path
    csv_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'extraction_results.csv')
    
    # Write results to CSV
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(['Entity (Query)', 'URL', 'Extracted Information'])
        for result in extraction_results:
            csvwriter.writerow([result['query'], result['url'], result['extracted_info']])
    
    # Send file as a downloadable attachment
    return send_file(csv_file_path, as_attachment=True)


@app.route('/update_google_sheet')
def update_google_sheet():
    # Retrieve extraction results from Redis
    stored_results = redis_db.get('extraction_results')
    if not stored_results:
        flash('No extraction results available to update the Google Sheet.')
        return redirect(url_for('home'))
    
    extraction_results = json.loads(stored_results)
    
    # Prepare data for Google Sheets
    data = [['Entity (Query)', 'URL', 'Extracted Information']]
    for result in extraction_results:
        data.append([result['query'], result['url'], result['extracted_info']])
    
    # Define spreadsheet ID and range (adjust as needed)
    spreadsheet_id = '<Your-Spreadsheet-ID>'
    range_name = 'Sheet1!A1'  # Starting cell, adjust based on your sheet layout
    
    # Use Sheets API to update the spreadsheet
    try:
        service = build('sheets', 'v4', credentials=credentials)
        body = {
            'values': data
        }
        service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='RAW',
            body=body
        ).execute()
        flash("Google Sheet updated successfully!")
    except Exception as e:
        flash(f"Failed to update Google Sheet: {e}")

    return redirect(url_for('check_stored_queries'))



# Route to display Google Sheets data
@app.route('/display_google_sheet_data', methods=['GET'])
def display_google_sheet_data():
    spreadsheet_id = '<Your-Spreadsheet-ID>'
    range_name = '<Your-Range>'  # For example, "Sheet1!A1:D10"
    try:
        data = read_google_sheet(spreadsheet_id, range_name)
        # Convert data to HTML table
        data_html = pd.DataFrame(data).to_html()
        return render_template('google_sheet.html', data_table=data_html)
    except Exception as e:
        flash(f"Error reading Google Sheet: {e}")
        return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
