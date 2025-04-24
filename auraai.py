from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage, AssistantMessage
from azure.core.credentials import AzureKeyCredential
import streamlit as st
from sqlalchemy import text, create_engine
from datetime import datetime
import pytz
import uuid 


utc = pytz.utc
ist = pytz.timezone("Asia/Kolkata")
server_os = 'posix'
# Initialize Streamlit app
st.title("AURA AI - The Future of Privacy")

# Configuration
engine = create_engine("sqlite:///aura.db", echo=True)
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4.1-nano"  
token = st.secrets["API_KEY"]  

get_tweets_query = text("""
SELECT u.id, u.picture, u.username, u.name, t.tweet, t.contains_image, t.image_path, t.created_at
FROM tweets t
LEFT JOIN users u ON t.user_id = u.id
ORDER BY created_at DESC
""")

def return_data():
    with engine.connect() as connection:
        tweets = connection.execute(get_tweets_query).fetchall()
        #print(f"Tweets: {tweets}")
        list_of_lists = []
        for tup in tweets:
            lst = list(tup)

            if len(lst) > 1 and isinstance(lst[1], str) and lst[1].startswith('static/'):
                lst[1] = lst[1].replace('static/', '')
                if server_os == "nt":
                    lst[1] = lst[1].replace("\\", "/")
            if len(lst) > 6 and isinstance(lst[6], str) and lst[6].startswith('static/'):
                lst[6] = lst[6].replace('static/', '')
                if server_os == "nt":
                    lst[6] = lst[6].replace("\\", "/")

            # Convert timestamp (index 7) to IST
            if len(lst) > 7 and isinstance(lst[7], str):
                try:
                    naive_dt = datetime.strptime(lst[7], "%Y-%m-%d %H:%M:%S")
                    aware_utc = utc.localize(naive_dt)
                    ist_time = aware_utc.astimezone(ist)
                    lst[7] = ist_time.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    print("Error converting time:", e)

            list_of_lists.append(lst)
        return list_of_lists
    
    
client = ChatCompletionsClient(
    endpoint=endpoint,
    credential=AzureKeyCredential(token),
)

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = model_name

if "messages" not in st.session_state:
    all_data = return_data()
    st.session_state.messages = [
        {"role": "system", "content": f"You are a helpful assistant that provides details about a Tweeting platform called Aura. You are the AURA AI. You will answer questions related to the tweets on the platoform. Platform also has a feature to post anonymous tweets, those tweets are sent by a Anonymous Username and name which is kept hidden for privacy. Answer any questions regarding all tweets. For Context here are all tweets: {all_data}."}
    ] 

for message in st.session_state.messages:
    if message["role"] != "system":  # Skip displaying the system prompt
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ]
        
        response_stream = client.complete(
            model=st.session_state["openai_model"],
            messages=messages,
            stream=True,
        )
        
        full_response = ""
        response_placeholder = st.empty()  
        for chunk in response_stream:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                response_placeholder.markdown(full_response)  
        
        
        st.session_state.messages.append({"role": "assistant", "content": full_response})