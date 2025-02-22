import streamlit as st
import os
import google.generativeai as genai  
import pickle
from PIL import Image
import io
import hashlib
import PyPDF2

# Set Streamlit page configuration
st.set_page_config(page_title="Welcome to Invoice Analyzer")

# Load API key from secrets
LLM_call = st.secrets.get("LLM_call")
if not LLM_call:
    st.error("API key not found. Please configure your secrets.")
else:
    genai.configure(api_key=LLM_call)

# Function to generate invoice ID (fix applied)
def generate_invoice_id(content):
    if isinstance(content, str):  
        return hashlib.md5(content.encode()).hexdigest()
    elif isinstance(content, bytes):  
        return hashlib.md5(content).hexdigest()
    else:
        raise ValueError("Unsupported content type for hashing")

# Function to get response from Gemini AI
def get_gemini_response(image_or_text, prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")  
    response = model.generate_content([image_or_text, prompt])
    return response.text if response else "Error: No response from LLM."

# Function to save invoice data to a pickle file
def save_to_pickle(data, filename="invoice_data.pkl"):
    existing_data = load_from_pickle(filename)
    existing_data.update(data)
    
    with open(filename, "wb") as f:
        pickle.dump(existing_data, f)

# Function to load invoice data from a pickle file
def load_from_pickle(filename="invoice_data.pkl"):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return pickle.load(f)
    else:
        return {}

# Streamlit UI
st.header("📄 Invoice Analyzer")

# File uploader for images & PDFs
uploaded_files = st.file_uploader("Upload invoice images or PDFs...", 
                                  type=["jpg", "jpeg", "png", "pdf"], 
                                  accept_multiple_files=True)

# Prompt for AI extraction
input_prompt = """
You are an expert in understanding invoices.
You will receive images of invoices and extract relevant details from them in a tabulated manner every time with the same format.
If a detail is not available, put 'NIL'.
"""

if uploaded_files:
    invoice_data = {}

    for uploaded_file in uploaded_files:
        content = None  # Initialize content variable

        if uploaded_file.type in ["image/jpeg", "image/png", "image/jpg"]:
            image = Image.open(uploaded_file)
            st.image(image, caption=f"📸 Uploaded: {uploaded_file.name}", use_container_width=True)
            content = image.tobytes()  # Convert image to bytes
        
        elif uploaded_file.type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            content = "".join([page.extract_text() or "" for page in pdf_reader.pages])  # Extract text
            st.text_area(f"📄 Extracted text from {uploaded_file.name}", content, height=300)

        else:
            st.error(f"Unsupported file type: {uploaded_file.type}")
            continue

        if content:
            invoice_id = generate_invoice_id(content)  # Generate unique ID for the invoice
            
            with st.spinner(f"⏳ Extracting details for {uploaded_file.name}..."):
                response = get_gemini_response(content, input_prompt)
            
            st.subheader(f"📜 Extracted Details for {uploaded_file.name}")
            st.write(response)
            
            # Store invoice details
            invoice_data[invoice_id] = {
                "filename": uploaded_file.name,
                "invoice_details": response
            }

    # Save data to pickle
    save_to_pickle(invoice_data)
    st.success("✅ All invoices saved in 'invoice_data.pkl'")

