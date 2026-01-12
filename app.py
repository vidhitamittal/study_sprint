import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF

genai.configure(api_key="yourAPIkey") # will need to be replaced with your actual API key
model = genai.GenerativeModel('gemini-3-flash-preview') # use the appropriate google gen ai model

st.set_page_config(page_title="AI Study Buddy", page_icon="🎓", layout="wide")

# Helper function to create the PDF file in memory
def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

# Helper function to extract text from uploaded PDF
def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content: text += content
    return text

st.title("🎓 AI Study Buddy")
st.markdown("### 📥 Step 1: Provide your content")

col1, col2 = st.columns(2)
with col1:
    st.info("Option A: Upload a PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

with col2:
    st.info("Option B: Paste Text")
    text_input = st.text_area("Paste notes here:", height=150)

if st.button("🚀 Generate Study Guide", use_container_width=True):
    final_text = ""
    if uploaded_file:
        final_text = extract_pdf_text(uploaded_file)
    elif text_input:
        final_text = text_input
    
    if final_text:
        with st.spinner('Reading your notes...'):
            prompt = f"Summarize the following notes into a high-level summary, key bullet points, and 3 test questions: {final_text[:15000]}"
            
            try:
                response = model.generate_content(prompt)
                study_guide_text = response.text
                
                st.success("Guide Generated!")
                st.markdown("### 📝 Your Custom Study Guide")
                st.write(study_guide_text)
                
                pdf_data = create_pdf(study_guide_text)
                st.download_button(
                    label="📥 Download Guide as PDF",
                    data=pdf_data,
                    file_name="study_guide.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please upload a file or paste text first.")
