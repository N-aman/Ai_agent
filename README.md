
# AI Agent Data Extraction and Query Generation

This project allows users to upload data from a CSV file or Google Sheets and generate custom queries for analyzing the data. The application extracts specific information from the data based on user-defined templates, and presents the results with options for further actions like downloading CSVs or processing the extracted data.

## Features

- **Upload CSV files**: Allows users to upload CSV files and preview their data.
- **Google Sheets integration**: Fetch data directly from a Google Sheets URL and preview it.
- **Custom query generation**: Users can generate custom search queries using data from the CSV or Google Sheets.
- **Extraction results**: After querying, the results are displayed with options to download them as CSV or process the data.
- **Responsive UI**: A clean and simple interface for easy navigation.

## Requirements

Before running the project, ensure that you have the following installed on your local machine:

- Python (>= 3.8)
- pip
- Virtual environment (optional but recommended)
- Redis server

### Install Dependencies

1. Clone the repository:

   ```bash
   git clone https://github.com/N-aman/Ai_agent.git
   ```

2. Navigate into the project directory:

   ```bash
   cd Ai_agent
   ```

3. Create and activate a virtual environment (optional but recommended):

   On macOS/Linux:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

   On Windows:

   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

4. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Set Up Google Sheets API

1. Create a project in the Google Developers Console.
2. Enable the Google Sheets API for your project.
3. Download the credentials JSON file and name it credentials.json.
4. Place credentials.json in the root directory of your project.
5. Make sure the Google Sheet you're accessing is shared with the email associated with the credentials.

## Set Up Redis
If you wish to store the generated queries in Redis (this step is optional):

1. Install and run Redis on your local machine.
2. Ensure that Redis is running on the default port 6380 (or configure it accordingly in the code).

### Part 2: Running the Application

## Running the Application

1. Start the Flask application by running:

   ```bash
   python app.py
   ```

2. The app will be available at http://127.0.0.1:5000 in your browser.

### Part 3: User Guide

## User Guide

### 1. Home Page (`/`)

On visiting the home page, you’ll see two options for data input:

- **Upload CSV File**: Allows you to upload a CSV file to the application.
- **Enter Google Sheets URL**: Allows you to input a URL for a Google Sheets file.

#### CSV File Upload

1. Click the **Choose File** button to select a CSV file from your computer.
2. Once selected, click **Upload and Preview**. The app will:
   - Upload the file.
   - Display the first 5 rows of the CSV for preview.
   - Store the data in the session for further use.

#### Google Sheets URL Input

1. Enter the URL of the Google Sheets document into the input field.
2. Click **Load Data** to fetch and display the data from the Google Sheet.

Once data is loaded from either source (CSV or Google Sheets), a preview of the data will be displayed below the upload options.

### 2. Generate Custom Queries (`/process_query`)

After uploading the CSV or loading data from Google Sheets, you will see the option to **Generate Custom Queries**.

1. **Custom Query Template**: In the input field, enter a query template with placeholders for the data columns (e.g., `Get the average salary of {Job_Title} in {Location}`). The placeholders should match the column names from your data.
   
2. **Generate Queries**: Once the template is provided, click **Generate Queries** to create the queries based on the data in the CSV or Google Sheets.

3. The generated queries will be displayed on the next page.

### 3. Extraction Results (`/extraction_results`)

After generating the queries, you will be shown the extraction results. Each row will have the following information:

- **Entity (Query)**: The query that was generated.
- **URL**: A clickable link to the source (if applicable).
- **Extracted Information**: The data that was extracted based on the query.

#### Available Actions:

- **Download CSV**: Download the extracted information as a CSV file for further use.
- **Go to Processed Data**: Navigate to a page where you can process the extracted data further.

### 4. Download CSV (`/download_csv`)

You can download the extracted data as a CSV file by clicking the **Download CSV** button on the extraction results page.

## Troubleshooting

### Error: `ConnectionError` or `Unable to fetch data from Google Sheets`

- **Cause**: This error can occur if there are issues with the Google Sheets API.
- **Solution**: Ensure that your `credentials.json` file is correct and that the Google Sheet is shared with the correct Google account.

### Error: `FileNotFoundError: 'credentials.json'`

- **Cause**: The application cannot find the `credentials.json` file.
- **Solution**: Make sure the `credentials.json` file is located in the root directory of your project.
