# 🤖 AI Resume Tailor & Application Assistant

A powerful Streamlit app that uses Groq AI to tailor your resume, generate cover letters, and craft perfect job application emails — all in one click.

## ✨ Features

### 📧 Email Mode
- **Tailored Resume PDF** — Customized to match the job description
- **Cover Letter PDF** — Professionally written and tailored
- **Email Subject** — One-click copy
- **Email Body** — One-click copy, mentions attached PDFs

### 🌐 Job Portal Mode
- **Tailored Resume PDF** — ATS-optimized for the specific job
- **Cover Letter PDF** — Matching the portal requirements
- **Q&A Answers** — Automatically detects and answers all portal questions
- **One-click copy** for every answer

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install LaTeX (for PDF generation)

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended
```

**macOS:**
```bash
brew install --cask mactex
```

**Windows:**
Download and install [MiKTeX](https://miktex.org/download)

### 3. Configure API Keys

Create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY_1 = "gsk_your_first_key_here"
GROQ_API_KEY_2 = "gsk_your_second_key_here"
GROQ_API_KEY_3 = "gsk_your_third_key_here"
```

**Supports up to 15 keys with automatic failover!**

### 4. Run the App

```bash
streamlit run app.py
```

## 📁 Project Structure

```
.
├── app.py                 # Main Streamlit application
├── requirements.txt     # Python dependencies
├── .streamlit/
│   └── secrets.toml      # API keys (DO NOT COMMIT)
└── README.md
```

## 🔑 API Key Formats Supported

The app automatically detects these formats in `secrets.toml`:

| Format | Example |
|--------|---------|
| Numbered keys | `GROQ_API_KEY_1`, `GROQ_API_KEY_2`, ... |
| Single key | `GROQ_API_KEY` |
| Comma-separated | `GROQ_API_KEYS = "gsk_xxx,gsk_yyy"` |
| Lowercase | `groq_api_key_1`, `groq_api_key` |

## 🎨 How It Works

1. **Select Mode** — Email or Job Portal
2. **Paste Job Text** — Full description or portal page
3. **Click Generate** — AI tailors everything in ~30 seconds
4. **Download PDFs** — Resume + Cover Letter
5. **Copy Text** — One-click copy for emails and answers

## 🛠️ Customization

### Change the Base Resume
Edit the `BASE_RESUME_LATEX` variable in `app.py` with your own LaTeX resume.

### Change the Cover Letter Template
Edit the `BASE_COVER_LETTER_LATEX` variable in `app.py`.

### Change the AI Model
Select from the sidebar:
- `llama-3.3-70b-versatile` (recommended)
- `llama-3.1-70b-versatile`
- `mixtral-8x7b-32768`
- `gemma2-9b-it`

## ⚠️ Important Notes

- **LaTeX Required**: PDF generation needs `pdflatex` installed. Without it, you'll get LaTeX source code to compile manually.
- **API Keys**: Never commit `secrets.toml` to git. Add it to `.gitignore`.
- **Rate Limits**: The app automatically rotates through your API keys if one hits a rate limit.

## 📝 License

MIT License — Free to use and modify.

---

**Built by Ibtasam Ahmad** | [LinkedIn](https://linkedin.com/in/ibtasam-ahmad) | [GitHub](https://github.com/Ibtasam-Ahmad)