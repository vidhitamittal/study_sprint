import re
import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF
import requests

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

genai.configure(api_key="") # will need to be replaced with your actual API key
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

# Helper function to pull readable text from a URL
def extract_website_text(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        raise ValueError(f"Unable to fetch the URL: {exc}")
    
    html = response.text
    if BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
    else:
        text = re.sub(r"<[^>]+>", " ", html)
    
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    cleaned_text = "\n".join(lines)
    if not cleaned_text:
        raise ValueError("No readable text found on the webpage.")
    
    return cleaned_text[:20000]  # safety limit to keep prompt size manageable

st.title("🎓 AI Study Buddy")
st.markdown("### 📥 Step 1: Provide your content")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("Option A: Upload a PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

with col2:
    st.info("Option B: Paste Text")
    text_input = st.text_area("Paste notes here:", height=150)

with col3:
    st.info("Option C: Enter a Website URL")
    website_url = st.text_input("URL:", placeholder="https://example.com")

if st.button("🚀 Generate Study Guide", use_container_width=True):
    final_text = ""
    if uploaded_file:
        final_text = extract_pdf_text(uploaded_file)
    elif text_input:
        final_text = text_input
    elif website_url:
        try:
            final_text = extract_website_text(website_url)
        except Exception as e:
            st.error(f"Could not read the website: {e}")
            final_text = ""
    
    if final_text:
        with st.spinner('Gathering your content...'):
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
        st.warning("Please upload a PDF, paste text, or provide a website URL.")
