
# AI Agent Data Extraction and Query Generation  

This project empowers users to upload data from a **CSV file** or **Google Sheets** and create custom queries to analyze and extract meaningful insights. By leveraging user-defined templates, the application generates queries specifically tailored to the uploaded data.  

The application performs web searches based on these queries, retrieves relevant results, and uses a powerful language model (LLM) to parse and extract the most accurate and useful information from the web results. The extracted insights are then presented in an organized format, along with options for further processing, downloading CSVs, or refining the results for deeper analysis.  

This streamlined process transforms raw data into actionable insights with minimal effort, saving time and boosting productivity.  

---

## Features  

- **Custom Query Generation:**  
  Create precise, user-defined queries for analyzing uploaded datasets.  

- **Web Search Integration:**  
  The application performs web searches based on the queries and retrieves relevant results.  

- **LLM-Powered Insight Extraction:**  
  Extract the most accurate and useful information from web results using a powerful language model.  

- **Organized Output:**  
  Present insights in a structured format, with options for further processing or downloading as CSVs.  

- **Deeper Analysis Tools:**  
  Refine the results and explore more advanced insights for a thorough understanding of the data.  

---

### Video Demonstration  
Check out this short video demonstration of the project in action: [Project Video Demonstration](#).  

---

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

### Create `api_keys.json`

To use this project, you need API keys for the following services:

- SerpAPI
- GroqAPI
- WebScrapingAPI

Create a JSON file named `api_keys.json` in the root directory of the project.

Use the following format for the file:

```json
{
  "serpapi": "YOUR_SERPAPI_KEY",
  "groqapi": "YOUR_GROQAPI_KEY",
  "webscrapingapi": "YOUR_WEBSCRAPINGAPI_KEY"
}
```

Replace `"YOUR_SERPAPI_KEY"`, `"YOUR_GROQAPI_KEY"`, and `"YOUR_WEBSCRAPINGAPI_KEY"` with your actual API keys for each service.

Save the file as `api_keys.json` and place it in the root directory of the project.

### Set Up Google Sheets API

To use this project with Google Sheets, you need to set up access to the Google Sheets API. Follow these detailed steps:

1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Log in with your Google account if not already logged in.
   - Click on **"Select a Project"** (top-left) and then click **"New Project"**.
   - Give your project a name (e.g., "AI Agent Project") and click **"Create"**.
   - Wait for the project to be created, then select it from the project list.

2. **Enable the Google Sheets API**:
   - While in your project, go to the **API & Services** > **Library** in the left-hand menu.
   - Search for **Google Sheets API** in the search bar.
   - Click on **Google Sheets API** from the results and then click the **"Enable"** button.

3. **Create Service Account Credentials**:
   - Navigate to **API & Services** > **Credentials** from the left-hand menu.
   - Click on the **"Create Credentials"** button at the top and select **Service Account**.
   - Provide a name for your service account (e.g., "AI Agent Service Account") and click **"Create and Continue"**.
   - Assign a role to the service account. Select **Basic** > **Editor**, then click **Continue** and **Done**.

4. **Generate a Credentials File**:
   - In the **Credentials** page, find the service account you just created.
   - Click on the **pencil icon** next to your service account to edit it.
   - Navigate to the **Keys** tab and click **"Add Key"**, then select **JSON**.
   - A JSON file containing your credentials will be downloaded. Rename this file to `credentials.json`.

5. **Place `credentials.json` in the Project**:
   - Move the downloaded `credentials.json` file into the root directory of your project.
   - Ensure that this file is included only in your local environment. (It is excluded by default if you followed the `.gitignore` setup.)

6. **Share Your Google Sheet with the Service Account**:
   - Open the Google Sheet you want to work with.
   - Click on the **Share** button in the top-right corner.
   - Copy the **Service Account Email** (visible in the `credentials.json` file under `"client_email"`) and paste it into the "Add people and groups" field in the sharing dialog.
   - Assign **Editor** access to the service account and click **Send**.

7. **Verify the Setup**:
   - Ensure that `credentials.json` exists in your project directory and is correctly configured.
   - The Google Sheet you are accessing should now be shared with your service account, allowing the application to read or write data to it.

By following these steps, you will have successfully configured access to the Google Sheets API for your project.


## Set Up Redis

1. Install and run Redis on your local machine. You can follow the [official Redis installation guide](https://redis.io/docs/getting-started/installation/) for your operating system.
2. Ensure that Redis is running on the port `6380` (or configure it accordingly in the code).

---

## Set Up Flask Secret Key
Flask requires a secret key for securely signing session cookies and other sensitive information. Follow these steps to create and add a Flask secret key to your project:

### Step 1: Generate a Secret Key
A Flask secret key can be any random string. You can generate a strong random key in Python using the `secrets` module:

1. Open a Python shell or a script.
2. Run the following command:

   ```python
   import secrets
   print(secrets.token_hex(24))
   ```

   This will output a secure random key, such as:

   ```
   ead32f9b0b6842a593ffecb3f1b1e5c042a17e65cfd28321
   ```

### Step 2: Add the Secret Key to `app.py`
1. Open your `app.py` file.
2. Locate or add the section where you configure Flask.
3. Add the following line, replacing `<your_secret_key>` with the key you generated:

   ```python
   app.secret_key = '<your_secret_key>'
   ```

   For example:

   ```python
   app.secret_key = 'ead32f9b0b6842a593ffecb3f1b1e5c042a17e65cfd28321'
   ```

### Step 3: (Optional) Store the Secret Key in a Secure Location
For added security, you can store the secret key in an environment variable instead of hardcoding it in your code. Here’s how:

1. Set the environment variable (example for Windows):
   ```bash
   set FLASK_SECRET_KEY=ead32f9b0b6842a593ffecb3f1b1e5c042a17e65cfd28321
   ```

   For macOS/Linux:
   ```bash
   export FLASK_SECRET_KEY=ead32f9b0b6842a593ffecb3f1b1e5c042a17e65cfd28321
   ```

2. Update `app.py` to load the key from the environment variable:

   ```python
   import os
   app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_key_if_not_set')
   ```

This approach ensures your secret key remains secure and is not exposed in your codebase.


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
   
2. **Generate Custom Queries (/process_query)**  
   - After uploading the CSV or loading data from Google Sheets, you will see the option to **Generate Custom Queries**.  
   - **Custom Query Template**: Enter a query template with placeholders for the data columns (e.g., *Get the average salary of {Job_Title} in {Location}*). The placeholders should exactly match the column names from your data.  
   - **Generate Queries**: Once the template is provided, click **Generate Queries** to create queries based on the data in the CSV or Google Sheets.  
   - The generated queries will be displayed on the next page for confirmation.  

3. **Search Results Display**  
   - After the queries are generated, the application performs searches using the queries.  
   - The **Search Results Page** displays the web results retrieved for each query.  
   - These results are shown so you can see the context of the data being extracted.  

4. **Extraction Results (Using LLM and Groq API)**  
   - After reviewing the search results, the application uses **Groq API** to parse the web results and extract the most relevant information based on the query.  
   - You are then directed to the **Extraction Results Page**, which shows:  
     - **Entity (Query)**: The original query.  
     - **URL**: A clickable link to the source (if applicable).  
     - **Extracted Information**: The processed data derived from the web results using the LLM.  
   - Available Actions:  
     - **Download CSV**: Download the extracted information as a CSV file for further use.  
     - **Go to Processed Data**: Navigate to the next step where you can process the extracted data further.  

5. **Further Process Results (/process_extracted_info_json)**  
   - On the **Processed Data Page**, you can refine and work with the extracted information.  
   - This page also provides an option to **Download the Final Processed Data** as a CSV file for your records or further analysis.  


## Troubleshooting

### Error: `ConnectionError` or `Unable to fetch data from Google Sheets`

- **Cause**: This error can occur if there are issues with the Google Sheets API.
- **Solution**: Ensure that your `credentials.json` file is correct and that the Google Sheet is shared with the correct Google account.

### Error: `FileNotFoundError: 'credentials.json'`

- **Cause**: The application cannot find the `credentials.json` file.
- **Solution**: Make sure the `credentials.json` file is located in the root directory of your project.
