# 🎓 Study Sprint: AI Study Buddy

**Study Sprint** is a lightweight, AI-powered educational tool that transforms dense lecture notes and messy text into structured, downloadable study guides. 



## ✨ Features
- **Smart Summarization:** Get a high-level 3-sentence overview of any topic.
- **Key Concepts:** Automatically extracts bulleted key terms and definitions.
- **Instant Quizzing:** Generates challenging multiple-choice questions to test your knowledge.
- **Dual Input:** Upload PDFs directly or paste raw text.
- **PDF Export:** Download your generated guide as a clean PDF for offline studying.

## 🛠️ Tech Stack
- **Frontend:** [Streamlit](https://streamlit.io/)
- **LLM:** [Google Gemini 1.5 Flash](https://ai.google.dev/)
- **PDF Processing:** `pypdf` (extraction) and `fpdf` (generation)

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- A Google Gemini API Key (Get one for free at [Google AI Studio](https://aistudio.google.com/))

### Installation
1. Clone the repository:
 - git clone [https://github.com/yourusername/Study Sprint.git](https://github.com/yourusername/Study Sprint.git)
 - cd Study Sprint
2. Install dependencies:
- pip install -r requirements.txt
3. Set up your API Key:
  - Create a .env file or replace the placeholder in app.py:
4. Run the app:
- streamlit run app.py
### 📝 Usage
- Open the app in your browser (usually localhost:8501).
- Upload a PDF of your notes OR paste your text into the box.
- Click Generate Study Guide.
- Review your guide on-screen and click Download Guide as PDF to save it.
### 🤝 Contributing
- Found a bug? Have a feature idea? Feel free to open an issue or submit a pull request!


