import re
import requests
import streamlit as st
from bs4 import BeautifulSoup
from pypdf import PdfReader
from fpdf import FPDF

class StudyBackend:
    @staticmethod
    @st.cache_data
    def extract_pdf_text(pdf_file):
        reader = PdfReader(pdf_file)
        return "".join([p.extract_text() for p in reader.pages if p.extract_text()])

    @staticmethod
    @st.cache_data
    def fetch_website_content(url):
        headers = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        return ' '.join(soup.get_text().split())[:12000]

    @staticmethod
    def get_prompt(guide_type, content):
        """Returns the specific prompt based on user selection"""
        prompts = {
            "📋 Comprehensive Summary": f"Summarize this into an executive summary, main topics with explanations, and a conclusion: {content}",
            "🎴 Flashcards": f"Create 15 flashcards. Format EXACTLY as: **Front:** [Q] **Back:** [A]. Content: {content}",
            "❓ Practice Questions": f"Create 10 MCQ questions with answers and 2 essay prompts: {content}",
            "🔑 Key Terms & Definitions": f"Extract and define 20 key terms with examples from this text: {content}",
            "📊 All-in-One": f"Create a full guide: Summary, 10 bullet points, 10 terms, and 5 practice questions: {content}"
        }
        return prompts.get(guide_type, prompts["📊 All-in-One"])

    @staticmethod
    def parse_flashcards(text):
        pattern = r'\*\*Front:\*\*\s*(.+?)\s*\*\*Back:\*\*\s*(.+?)(?=\*\*Front:|$)'
        matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
        return [{'front': f.strip(), 'back': b.strip()} for f, b in matches]

    @staticmethod
    def create_pdf_binary(text):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        clean_text = text.encode('latin-1', 'ignore').decode('latin-1')
        pdf.multi_cell(0, 10, txt=clean_text)
        return pdf.output(dest='S').encode('latin-1')
