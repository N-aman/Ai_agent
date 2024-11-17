import requests
import redis
import groq
import json


# Load the API keys from the JSON file
with open("api_keys.json", "r") as file:
    api_keys = json.load(file)

# Access the keys
serpapi_key = api_keys["serpapi"]
groqapi_key = api_keys["groqapi"]
webscrapingapi_key = api_keys["webscrapingapi"]

# Set up Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6380, db=0)

def parse_web_results(search_results, query):
    parsed_data = []
    
    # Debugging: print available queries and search results structure
    print("Available queries in search_results:", search_results.keys())  # Debugging line
    
    # Assuming search_results is a dictionary of queries and their corresponding results
    query_results = search_results.get(query, [])
    print(f"Query results for '{query}':", query_results)  # Debugging line
    
    if query_results:
        # Select the first result (or other criteria) for the query
        first_result = query_results[0]
        url = first_result.get('link')
        snippet = first_result.get('snippet', '')
        
        if url:
            parsed_data.append({'url': url, 'snippet': snippet})
        else:
            parsed_data.append({'url': None, 'snippet': snippet})

        print(f"Processed result for query '{query}': {first_result}")  # Debugging line
    
    return parsed_data



def fetch_and_store_content(url, api_key):
    # Check if content is already stored in Redis
    if redis_client.exists(url):
        print(f"Content for {url} already in Redis. Skipping fetch.")
        return redis_client.get(url)  # Return the cached content
    
    # If not cached, fetch from the web using the scraping API
    response = requests.get(f'https://api.webscrapingapi.com/v1?api_key={api_key}&url={url}')
    if response.status_code == 200:
        content = response.text
        redis_client.set(url, content)
        print(f"Content fetched and stored for {url}")  # Debugging line
        return content
    else:
        print(f"Error fetching content from {url}: {response.status_code}")
        return None


import os
import redis
from groq import Groq

# Set up Redis connection
redis_client = redis.StrictRedis(host='localhost', port=6380, db=0)

# Initialize Groq client
client = Groq(api_key=groqapi_key)

# Function to extract information using Groq
def extract_information_with_llm(url, snippet, initial_query):
    # Fetch content from Redis, or use an empty string if not available
    content = redis_client.get(url).decode('utf-8') if redis_client.exists(url) else ''
    
    # Construct the system prompt for the LLM
    system_prompt = {
        "role": "system",
        "content": "You are a helpful assistant. You reply with very short and concise answers, providing only the specific information requested."
    }

    # Append the user query as part of the chat history
    user_prompt = {
        "role": "user",
        "content": f"Given the snippet: '{snippet}' and full content: '{content}', please answer the following question: '{initial_query}'."
    }

    # Initialize chat history with the system prompt
    chat_history = [system_prompt, user_prompt]

    try:
        # Make the request to the Groq API to get the response
        response = client.chat.completions.create(
            model="llama3-70b-8192",  # Use a Groq-supported model
            messages=chat_history,
            max_tokens=100,
            temperature=0.2
        )

        # Extract the answer from the response
        extracted_info = response.choices[0].message.content.strip()  # Get the answer from the assistant
        
        # Debugging line: output the extracted information
        print(f"Extracted Info for {url}: {extracted_info}")

        return extracted_info

    except Exception as e:
        # Handle errors in the Groq API call
        print(f"Error in LLM call: {str(e)}")
        return None
