# 🤖 AI Resume Tailor & Application Assistant

A Streamlit app that heavily tailors a **fixed master resume + cover letter** to a specific job
description using **Groq AI**, adapts the relocation wording to the job's **location & work mode**,
and lets you **review and edit everything before the PDF is built**.

The master resume and cover letter are **hardcoded** in `app.py` (for Ibtasam Ahmad) — you never
upload anything. Paste a job description, review the tailored draft, tweak if needed, approve, download.

## ✨ Features

- **Heavy JD tailoring** — summary, skills order, project order, and bullets are rewritten around the
  job description (truthfully — it never invents employers, numbers, or projects).
- **Location & work-mode aware relocation wording:**
  | Setting | What the documents say |
  |---|---|
  | **Remote** | Relocation lines removed; remote-collaboration strengths emphasized |
  | Location = **Lahore** (home) | Presented as a **local** candidate — no relocation |
  | Location = elsewhere (Onsite/Hybrid) | "Immediately available to relocate to **{that city}**" |
- **Two application modes:**
  - **📧 Email** — tailored resume PDF + cover letter PDF + application email (subject + body)
  - **🌐 Job Portal** — tailored resume PDF + cover letter PDF + auto-detected Q&A answers
- **Review → Edit → Approve gate** — the AI shows *what it changed* plus editable boxes; the PDFs are
  compiled from **exactly what you approve**.
- **Multi-key Groq failover** — rotates keys only on rate-limit / auth / connection errors.

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Install LaTeX (for PDF output)
- **Ubuntu/Debian:** `sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended`
- **macOS:** `brew install --cask mactex`
- **Windows:** install [MiKTeX](https://miktex.org/download)

> Without `pdflatex`, the app still works — it gives you the `.tex` source to compile (e.g. on Overleaf).

### 3. Add your Groq API key(s)
Edit `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY_1 = "gsk_your_first_key_here"
GROQ_API_KEY_2 = "gsk_your_second_key_here"   # optional, for failover
```
Also supported: single `GROQ_API_KEY`, or comma-separated `GROQ_API_KEYS = "gsk_a,gsk_b"`.

### 4. Run
```bash
streamlit run app.py
```

## 🎨 How it works
1. Choose **mode** (Email / Job Portal), **work mode** (Onsite / Hybrid / Remote), and **job location**.
2. Paste the full job description (for Portal mode, paste the whole page including questions).
3. Click **Generate & Review**.
4. Read the **"What changed"** summary, edit the resume/cover/email/answers if you want.
5. Click **✅ Approve & Build PDFs** → download.

## 🛠️ Customization
- **Resume / cover letter:** edit `BASE_RESUME_LATEX` / `BASE_COVER_LETTER_LATEX` in `app.py`.
- **Home base:** edit `HOME_CITY` / `HOME_COUNTRY` (controls the local-vs-relocate logic).
- **Models:** pick in the sidebar (`llama-3.3-70b-versatile` recommended). Deprecated Groq models
  (e.g. `mixtral-8x7b-32768`) have been removed from the list.

## 📝 License
MIT — free to use and modify.

---
**Built by Ibtasam Ahmad** | [LinkedIn](https://linkedin.com/in/ibtasam-ahmad) | [GitHub](https://github.com/Ibtasam-Ahmad)
