import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

genai.configure(api_key="YOUR_ACTUAL_API_KEY_HERE")
model = genai.GenerativeModel('gemini-3-flash-preview')

st.set_page_config(page_title="AI Study Buddy", page_icon="🎓", layout="wide")

st.title("🎓 Study Sprint")
st.markdown("Transform your notes into a structured study guide instantly.")

# 2. Main Page Layout
st.markdown("### 📥 Step 1: Provide your content")

# Create two columns for the input methods
col1, col2 = st.columns(2)

with col1:
    st.info("Option A: Upload a PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

with col2:
    st.info("Option B: Paste Text")
    text_input = st.text_area("Paste notes here:", height=150)

# Helper function to read PDF
def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content
    return text

# 3. Processing Logic
if st.button("🚀 Generate Study Guide", use_container_width=True):
    final_text = ""
    
    # Check PDF first, then Text Area
    if uploaded_file:
        final_text = extract_pdf_text(uploaded_file)
    elif text_input:
        final_text = text_input
    
    if final_text:
        with st.spinner('Reading your notes and creating a guide...'):
            prompt = f"""
            You are an expert academic tutor. Summarize the following text into:
            1. A 3-sentence high-level summary.
            2. 5 Key Bullet Points.
            3. A 'Self-Test' section with 3 challenging multiple-choice questions.
            
            Text: {final_text[:15000]} 
            """
            
            try:
                response = model.generate_content(prompt)
                st.success("Done!")
                st.markdown("---")
                st.markdown("### 📝 Your Custom Study Guide")
                st.write(response.text)
            except Exception as e:
                st.error(f"An error occurred: {e}")
    else:
        st.warning("Please upload a PDF or paste some text first!")
