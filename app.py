import streamlit as st  # Import Streamlit before setting page config
import os  # Add this line to fix the missing os module error

# Set Page Configuration (MUST BE FIRST)
st.set_page_config(page_title="Welcome to Invoice Analyzer")

import google.generativeai as genai  
import pickle
from PIL import Image
import io
import hashlib

# Get API Key from Streamlit secrets
LLM_call = st.secrets.get("LLM_call")  # Using .get to avoid errors if key is missing
if not LLM_call:
    st.error("API key not found. Please configure your secrets.")
else:
    genai.configure(api_key=LLM_call)  # Configure Gemini API with the API key

# Function to get response from Gemini AI
def get_gemini_response(image, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")  
    response = model.generate_content([image, prompt])
    return response.text if response else "Error: No response from LLM."

# Function to generate a unique ID for each invoice
def generate_invoice_id(image):
    """Generates a unique hash ID for the invoice using image bytes."""
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    return hashlib.md5(image_bytes.getvalue()).hexdigest()  # Unique ID for each image

# Function to save extracted data to a pickle file
def save_to_pickle(data, filename="invoice_data.pkl"):
    """Saves extracted invoice details to a pickle file (appending new invoices)."""
    existing_data = load_from_pickle(filename)  # Load existing data
    existing_data.update(data)  # Add new invoice(s)
    
    with open(filename, "wb") as f:
        pickle.dump(existing_data, f)

# Function to load previously saved invoice data
def load_from_pickle(filename="invoice_data.pkl"):
    """Loads extracted invoice details from a pickle file."""
    if os.path.exists(filename):  # Use os to check if file exists
        with open(filename, "rb") as f:
            return pickle.load(f)
    else:
        return {}
