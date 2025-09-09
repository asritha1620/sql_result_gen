import streamlit as st
import requests
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

st.title("Text-to-SQL-Output")
st.markdown("Ask questions about company finance and cargo operations.")

# Initialize session state for chat history
if 'history' not in st.session_state:
    st.session_state.history = []

# Clear chat button
if st.sidebar.button("Clear Chat"):
    st.session_state.history = []
    st.rerun()

# Display chat history
for message in st.session_state.history:
    with st.chat_message(message['role']):
        st.write(message['content'])
        if 'timestamp' in message:
            st.caption(f"Sent at {message['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

# Chat input
question = st.chat_input("Enter your natural language question:")

if question:
    # Add user message to history
    st.session_state.history.append({'role': 'user', 'content': question, 'timestamp': datetime.now()})
    
    with st.chat_message('user'):
        st.write(question)
    
    with st.spinner("Generating response..."):
        try:
            response = requests.post("http://localhost:8000/query", json={"question": question}, timeout=30)
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "No response")
                
                # Add assistant message to history
                st.session_state.history.append({'role': 'assistant', 'content': response_text, 'timestamp': datetime.now()})
                
                with st.chat_message('assistant'):
                    st.write(response_text)
            else:
                error_msg = f"API Error: {response.status_code} - {response.text}"
                st.session_state.history.append({'role': 'assistant', 'content': error_msg, 'timestamp': datetime.now()})
                with st.chat_message('assistant'):
                    st.error(error_msg)
        except requests.exceptions.Timeout:
            error_msg = "Request timed out. Please try again."
            st.session_state.history.append({'role': 'assistant', 'content': error_msg, 'timestamp': datetime.now()})
            with st.chat_message('assistant'):
                st.error(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Unable to connect to the API: {str(e)}. Please ensure the FastAPI server is running."
            st.session_state.history.append({'role': 'assistant', 'content': error_msg, 'timestamp': datetime.now()})
            with st.chat_message('assistant'):
                st.error(error_msg)

