import streamlit as st
import google.generativeai as genai
from backend import StudyBackend

api_key = st.secrets["GOOGLE_API_KEY"]
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')

def render_flashcards(flashcards):
    st.subheader("🎴 Your Study Deck")
    cols = st.columns(2)
    for idx, card in enumerate(flashcards):
        with cols[idx % 2]:
            state_key = f"flip_state_{idx}"
            if state_key not in st.session_state:
                st.session_state[state_key] = False
            
            is_flipped = st.session_state[state_key]
            content = card['back'] if is_flipped else card['front']
            color = "#C850C0" if is_flipped else "#4158D0"
            
            st.markdown(f"""<div style="background-color: {color}; padding: 30px; border-radius: 15px; 
                min-height: 150px; color: white; text-align: center; display: flex; 
                align-items: center; justify-content: center; font-size: 1.1rem; margin-bottom: 10px;">
                {content}</div>""", unsafe_allow_html=True)
            
            if st.button(f"Flip Card {idx+1}", key=f"btn_card_{idx}", use_container_width=True):
                st.session_state[state_key] = not st.session_state[state_key]
                st.rerun()

def main():
    st.set_page_config(page_title="AI Study Buddy", layout="wide")
    st.title("🎓 AI Study Buddy")

    if 'source_text' not in st.session_state:
        st.session_state.source_text = ""

    st.markdown("### 📥 Step 1: Provide Content")
    tab1, tab2, tab3 = st.tabs(["📄 Upload PDF", "✍️ Paste Text", "🌐 Website URL"])
    
    with tab1:
        file = st.file_uploader("Upload PDF", type="pdf")
        if file: st.session_state.source_text = StudyBackend.extract_pdf_text(file)
    with tab2:
        st.session_state.source_text = st.text_area("Paste notes", value=st.session_state.source_text, height=150)
    with tab3:
        url = st.text_input("URL")
        if st.button("Fetch Content"):
            try:
                st.session_state.source_text = StudyBackend.fetch_website_content(url)
                st.success("Loaded!")
            except Exception as e: st.error(f"Error: {e}")

    st.divider()
    st.markdown("### ⚙️ Step 2: Select Guide Type")
    c1, c2 = st.columns([3, 1])
    
    with c1:
        # Full list of options now included
        guide_type = st.selectbox("Format", [
            "📋 Comprehensive Summary", 
            "🎴 Flashcards", 
            "❓ Practice Questions", 
            "🔑 Key Terms & Definitions", 
            "📊 All-in-One"
        ], label_visibility="collapsed")
    with c2:
        generate_clicked = st.button("🚀 Generate Guide", use_container_width=True)

    if generate_clicked:
        if not st.session_state.source_text:
            st.warning("Please provide content first!")
        else:
            with st.spinner("AI is thinking..."):
                # Get specific prompt from backend
                prompt = StudyBackend.get_prompt(guide_type, st.session_state.source_text[:10000])
                response = model.generate_content(prompt)
                st.session_state.raw_result = response.text
                
                # Handle flashcard parsing only if that mode is selected
                if "Flashcards" in guide_type:
                    st.session_state.active_flashcards = StudyBackend.parse_flashcards(response.text)
                else:
                    st.session_state.active_flashcards = None

    if "raw_result" in st.session_state:
        st.divider()
        if st.session_state.get("active_flashcards"):
            render_flashcards(st.session_state.active_flashcards)
        else:
            st.markdown(st.session_state.raw_result)
        
        pdf_bytes = StudyBackend.create_pdf_binary(st.session_state.raw_result)
        st.download_button("📥 Download PDF", data=pdf_bytes, file_name="study_guide.pdf")

if __name__ == "__main__":
    main()
