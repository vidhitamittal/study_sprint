import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

genai.configure(api_key="youAPIkey") # will need to be replaced with your actual API key
model = genai.GenerativeModel('gemini-3-flash-preview') # use the appropriate google gen ai model

st.set_page_config(page_title="AI Study Buddy", page_icon="🎓", layout="wide")

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
    
    pdf.multi_cell(0, 10, txt=clean_text)
    return pdf.output(dest='S').encode('latin-1')

def extract_pdf_text(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        content = page.extract_text()
        if content: text += content
    return text

def fetch_website_content(url):
    """Fetch and extract text content from a website URL"""
    try:
        url = url.strip()
        url = url.rstrip('/')
        parsed = urlparse(url)
        if not parsed.scheme:
            url = 'https://' + url
            parsed = urlparse(url)
        
        if not parsed.netloc:
            raise ValueError("Invalid URL format. Please include the full URL (e.g., https://example.com)")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', '').lower()
        if 'html' not in content_type:
            raise ValueError(f"URL does not point to an HTML page. Content-Type: {content_type}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        if not text or len(text.strip()) < 50:
            raise ValueError("Could not extract meaningful content from the webpage. The page might be empty or require JavaScript to load content.")
        
        return text[:15000] 
        
    except requests.exceptions.ConnectionError as e:
        raise Exception(f"Connection failed. Please check:\n1. Your internet connection\n2. The URL is correct and accessible\n3. The website is not blocking requests\n\nOriginal error: {str(e)}")
    except requests.exceptions.Timeout:
        raise Exception("Request timed out. The website took too long to respond. Please try again.")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"HTTP error: {e.response.status_code} - {e.response.reason}. The website may require authentication or the page doesn't exist.")
    except ValueError as e:
        raise Exception(str(e))
    except Exception as e:
        raise Exception(f"Error fetching website: {str(e)}")

st.title("🎓 AI Study Buddy")
st.markdown("### 📥 Step 1: Provide your content")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("Option A: Upload a PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", key="pdf_uploader")

with col2:
    st.info("Option B: Paste Text")
    text_input = st.text_area("Paste notes here:", height=150, key="text_input")

with col3:
    st.info("Option C: Enter Website URL")
    url_input = st.text_input("Enter website URL:", placeholder="https://example.com/article", key="url_input")

if st.button("🚀 Generate Study Guide", use_container_width=True):
    final_text = ""
    if uploaded_file:
        final_text = extract_pdf_text(uploaded_file)
    elif text_input:
        final_text = text_input
    elif url_input:
        try:
            with st.spinner('Fetching website content...'):
                final_text = fetch_website_content(url_input)
                st.success("Website content fetched successfully!")
        except Exception as e:
            st.error(f"❌ {str(e)}")
            st.info("💡 **Tips:**\n- Make sure the URL is complete (e.g., https://www.example.com/page)\n- Check that the website is publicly accessible\n- Some websites block automated requests")
            final_text = ""
    
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
        st.warning("Please upload a file, paste text, or enter a URL first.")
