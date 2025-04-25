from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
import streamlit as st
# Configuration
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4.1-nano"  # Replace with your desired model
api_key = st.secrets["API_KEY"]  # Replace with your actual API key

# Initialize Azure client
client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(api_key),
)

# Function to send a prompt and get a response
def summarizer(tweet):
    # Prepare the messages for the API
    prompt = f"Explain the following tweet:\n\n Username: {tweet[2]}, Name: {tweet[3]}, Tweet: {tweet[4]}, time posted at: {tweet[7]}. Keep it small and concise about 4-5 lines. If there is no username or name, the tweet is wrote anonymously."
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]

    try:
        # Call the Azure API to get a single response
        response = client.complete(
            model=model_name,
            messages=messages,
            stream=False,  # Ensure streaming is disabled
        )

        # Extract the assistant's reply
        if response.choices and response.choices[0].message.content:
            print(f"Response: {response.choices[0].message.content.strip()}")
            return response.choices[0].message.content.strip()
        else:
            return "No response received from the model."
    except Exception as e:
        return f"An error occurred: {e}"