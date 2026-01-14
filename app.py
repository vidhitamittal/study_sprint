import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
from fpdf import FPDF
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

genai.configure(api_key="AIzaSyAMuNAtfBC-9fwqiylyqPLN8iO6KR2HJbU") # will need to be replaced with your actual API key
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
    
def generate_study_guide(content, guide_type):
    """Generate study guide based on selected type"""
    prompts = {
        "📋 Comprehensive Summary": f"""Create a comprehensive study guide from the following content. Include:
1. Executive Summary (2-3 sentences)
2. Main Topics with detailed explanations
3. Key Concepts
4. Important Details
5. Conclusion

Content: {content[:15000]}""",
        
        "🎴 Flashcards": f"""Create flashcards from the following content. Format each flashcard EXACTLY as follows:

**Front:** [Question or Term]
**Back:** [Answer or Definition]

**Front:** [Question or Term]
**Back:** [Answer or Definition]

Generate 15-20 flashcards covering the most important concepts. Make sure each flashcard follows the exact format above.

Content: {content[:15000]}""",
        
        "Practice Questions": f"""Create practice questions from the following content. Include:
1. 10 Multiple Choice Questions (with 4 options each and correct answer marked)
2. 5 Short Answer Questions (with sample answers)
3. 2 Essay Questions (with key points to include)

Content: {content[:15000]}""",
        
        "🔑 Key Terms & Definitions": f"""Extract and define key terms from the following content. For each term, provide:
1. The term
2. Definition
3. Context/Example from the content

List at least 20-25 key terms.

Content: {content[:15000]}""",
        
        "📊 All-in-One": f"""Create a complete study guide from the following content including:
1. High-level summary (2-3 paragraphs)
2. Key bullet points (10-15 points)
3. Important terms and definitions (10-15 terms)
4. Practice questions (5 questions with answers)
5. Study tips

Content: {content[:15000]}"""
    }
    
    return prompts.get(guide_type, prompts["📊 All-in-One"])

import re

def parse_flashcards(text):
    """Parse flashcard text into front/back pairs"""
    flashcards = []
    
    # Try to find patterns like "Front:" and "Back:"
    pattern = r'\*\*Front:\*\*\s*(.+?)\s*\*\*Back:\*\*\s*(.+?)(?=\*\*Front:|$)'
    matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    
    if matches:
        for front, back in matches:
            flashcards.append({
                'front': front.strip(),
                'back': back.strip()
            })
    else:
        # Fallback: try to split by lines and look for Q/A patterns
        lines = text.split('\n')
        current_front = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if 'front:' in line.lower() or 'question:' in line.lower() or 'term:' in line.lower():
                current_front = re.sub(r'^(front|question|term):\s*', '', line, flags=re.IGNORECASE).strip()
            elif 'back:' in line.lower() or 'answer:' in line.lower() or 'definition:' in line.lower():
                if current_front:
                    back = re.sub(r'^(back|answer|definition):\s*', '', line, flags=re.IGNORECASE).strip()
                    flashcards.append({'front': current_front, 'back': back})
                    current_front = None
    
    return flashcards

def display_flashcards(flashcards):
    """Display flashcards in an interactive card format"""
    if not flashcards:
        st.warning("Could not parse flashcards. Showing raw text instead.")
        return False
    
    st.markdown("### 🎴 Interactive Flashcards")
    st.markdown("💡 *Click on a card to flip it and see the answer*")
    
    # Initialize session state for flashcard visibility
    if 'flashcard_states' not in st.session_state:
        st.session_state.flashcard_states = {}
    
    # Display flashcards in a grid
    num_cols = 2
    for i in range(0, len(flashcards), num_cols):
        cols = st.columns(num_cols)
        for j, col in enumerate(cols):
            if i + j < len(flashcards):
                card = flashcards[i + j]
                card_id = f"card_{i+j}"
                
                # Initialize state for this card
                if card_id not in st.session_state.flashcard_states:
                    st.session_state.flashcard_states[card_id] = False
                
                with col:
                    # Create clickable card
                    is_flipped = st.session_state.flashcard_states[card_id]
                    
                    # Card styling
                    card_html = f"""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        border-radius: 15px;
                        padding: 30px;
                        margin: 10px 0;
                        min-height: 200px;
                        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
                        cursor: pointer;
                        transition: transform 0.3s;
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        text-align: center;
                    ">
                        <div style="font-size: 18px; font-weight: 500;">
                            {card['front'] if not is_flipped else card['back']}
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    # Flip button
                    if st.button(f"🔄 Flip Card {i+j+1}", key=f"flip_{i+j}", use_container_width=True):
                        st.session_state.flashcard_states[card_id] = not st.session_state.flashcard_states[card_id]
                        st.rerun()
                    
                    # Show which side is visible
                    side_indicator = "❓ Question" if not is_flipped else "✅ Answer"
                    st.caption(f"{side_indicator} | Card {i+j+1} of {len(flashcards)}")
    
    return True


# Check if we have flashcards in session state (from a previous generation)
if 'flashcards' in st.session_state and 'study_guide_text' in st.session_state:
    st.title("🎓 AI Study Buddy")
    
    if display_flashcards(st.session_state.flashcards):
        with st.expander("📄 View Raw Text"):
            st.write(st.session_state.study_guide_text)
    
    st.markdown("---")
    st.markdown("### Generate New Study Guide")
    
    
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

st.markdown("### ⚙️ Step 2: Customize your study guide")
study_guide_type = st.selectbox(
    "Choose study guide format:",
    ["📋 Comprehensive Summary", "🎴 Flashcards", "❓Practice Questions", "🔑 Key Terms & Definitions", "📊 All-in-One"],
    help="Select the format that best suits your study needs"
)

if st.button("🚀 Generate Study Guide", use_container_width=True):
    # Clear previous flashcards when generating new ones
    if 'flashcards' in st.session_state:
        del st.session_state.flashcards
    if 'flashcard_states' in st.session_state:
        del st.session_state.flashcard_states
    
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
        with st.spinner(f'Generating {study_guide_type}...'):
            prompt = generate_study_guide(final_text, study_guide_type)
            
            try:
                response = model.generate_content(prompt)
                study_guide_text = response.text
                
                st.success("Guide Generated!")
                
                # Special handling for flashcards
                if study_guide_type == "🎴 Flashcards":
                    # Store flashcards in session state so they persist across reruns
                    flashcards = parse_flashcards(study_guide_text)
                    st.session_state.flashcards = flashcards
                    st.session_state.study_guide_text = study_guide_text
                    
                    if display_flashcards(flashcards):
                        # Show raw text in expander for reference
                        with st.expander("📄 View Raw Text"):
                            st.write(study_guide_text)
                    else:
                        # If parsing failed, show raw text
                        st.markdown(f"### 📝 Your {study_guide_type}")
                        st.write(study_guide_text)
                else:
                    st.markdown(f"### 📝 Your {study_guide_type}")
                    st.write(study_guide_text)
                
                # Add export options
                col_download1, col_download2 = st.columns(2)
                
                with col_download1:
                    pdf_data = create_pdf(study_guide_text)
                    st.download_button(
                        label="📥 Download as PDF",
                        data=pdf_data,
                        file_name=f"study_guide_{study_guide_type.replace(' ', '_').lower()}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                
                with col_download2:
                    txt_data = study_guide_text.encode('utf-8')
                    st.download_button(
                        label="📄 Download as TXT",
                        data=txt_data,
                        file_name=f"study_guide_{study_guide_type.replace(' ', '_').lower()}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please upload a file, paste text, or enter a URL first.")
