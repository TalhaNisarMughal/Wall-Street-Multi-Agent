import os, json
import uuid
import requests
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
from src.Chatbot.bot import Bot

load_dotenv()
root_dir = Path.cwd()

if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())
if "model_initialized" not in st.session_state:
    st.session_state["model_initialized"] = True
    bot = Bot()
    st.session_state["bot"] = bot
else:
    bot = st.session_state["bot"]
if "messages" not in st.session_state:
    st.session_state.messages = []
if "disabled" not in st.session_state:
    st.session_state["disabled"] = False
            
st.title("Builder APP")

for message in st.session_state.messages:
     with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Query"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)
    assistant_message_placeholder = st.empty()
    with assistant_message_placeholder.chat_message("assistant"):
        stream_container = st.empty()
        
        with st.spinner("Thinking..."):
            
            # endpoint = os.getenv('API_URL')
            endpoint = os.getenv('LOCALHOST_API_URL')
            payload = {
                "user_query": prompt,
                "user_id": st.session_state["user_id"],
            }
            
            response = requests.post(endpoint, json=payload, stream=True)
            if response.status_code == 200:
                response = response.text.replace('"', '')
                stream_container.markdown(response)
            # content_response = ""
            # # Display translation result
            # if response.status_code == 200:
            #     for token in response.iter_content(512):
            #         if token:
            #             token = token.decode('utf-8')
            #             content_response += token
            #             stream_container.markdown(content_response)
                human_message = {'question':  prompt}
                ai_message = {'output_key': response}
                
            else:
                print(response)
        
        file_path = os.path.join(root_dir, "state_management/state_management_dictionary.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as json_file:
                loaded_dict = json.load(json_file)
            with st.sidebar:
                st.write("# Context")
                st.markdown(loaded_dict["context"])

        st.session_state.messages.append(
            {"role": "assistant", "content": response})