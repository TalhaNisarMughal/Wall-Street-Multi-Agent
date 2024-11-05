import streamlit as st
import json
import time, os
from pathlib import Path

# Define the path for the shared storage file
ROOT_DIR = Path.cwd()
STORAGE_FILE = os.path.join(ROOT_DIR, "src/state_management/operator_response.json")

st.title("Operator Assistance Interface")

# Function to read from the JSON storage file
def read_storage():
    try:
        with open(STORAGE_FILE, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return {"bot_query": "", "operator_response": ""}
    except json.JSONDecodeError:
        return {"bot_query": "", "operator_response": ""}

# Function to write the operator response back to the JSON storage file
def write_storage(data):
    with open(STORAGE_FILE, "w") as file:
        json.dump(data, file)

# Poll the JSON file for a new bot query
while True:
    data = read_storage()
    bot_query = data.get("bot_query")

    if bot_query:
        st.subheader("Bot Query:")
        st.markdown(bot_query)

        operator_response = st.text_area("Type your response here...", key="operator_response")
        
        if st.button("Submit Response"):
            if operator_response:
                # Update JSON with the operator's response
                data["operator_response"] = operator_response
                write_storage(data)
                st.success("Response sent to bot!")
                
                # Clear the bot query after responding
                data["bot_query"] = ""
                write_storage(data)
            else:
                st.warning("Please provide a response before submitting.")
        break  # Stop polling once a query is displayed
    else:
        # Wait before checking the file again
        time.sleep(1)
