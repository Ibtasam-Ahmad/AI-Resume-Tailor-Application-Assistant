# 🤖 AI Resume Tailor & Application Assistant

A Streamlit app that heavily tailors a **fixed master resume + cover letter** to a specific job
description using your choice of **LLM provider** (Groq / OpenAI / OpenRouter / NVIDIA / Gemini),
adapts the relocation wording to the job's **location & work mode**,
and lets you **review and edit everything before the PDF is built**.

**Live Preview** : https://ai-resume-tailor-application-assistant.streamlit.app/

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
- **Full 7-step tailoring** — recruiter weak-spot audit, JD-aligned summary, quantified bullets,
  gap/transition reframed as growth, ATS keywords, project reordering, and a bold one-line
  **elevator pitch** embedded in the résumé summary, cover-letter close, and email signature.
- **Never truncates** — detects when a model hits its output cap and **auto-continues** the LaTeX
  until `\end{document}`, so long 3–4 page resumes come out complete.
- **Review → Edit → Approve gate** — the AI shows *what it changed* plus editable boxes; you can
  **compile & preview the rendered PDF inline** before downloading, and the PDFs are built from
  **exactly what you approve**.
- **Multi-provider, auto-detected** — configure a key for **Groq, OpenAI, OpenRouter, NVIDIA, or
  Gemini** and the app uses that provider automatically. Pick a preset model or enter a custom one.
- **Multi-key failover** — each provider rotates its keys only on rate-limit / auth / connection errors.

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

### 3. Add an API key for any one provider
Edit `.streamlit/secrets.toml` (see `secrets.toml.example`). Configure **any one** of:
```toml
GROQ_API_KEY_1     = "gsk_..."     # Groq
OPENAI_API_KEY     = "sk-..."      # OpenAI
OPENROUTER_API_KEY = "sk-or-..."   # OpenRouter
NVIDIA_API_KEY     = "nvapi-..."   # NVIDIA NIM
GEMINI_API_KEY     = "AIza..."     # Google Gemini
```
The app auto-detects which provider is present. Multiple keys per provider are supported for
failover (`GROQ_API_KEY_1`, `_2`, … or comma-separated `GROQ_API_KEYS = "gsk_a,gsk_b"`); the same
`_1/_2/…` and plural pattern works for every provider. If you configure more than one provider you
can switch between them in the sidebar.

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
- **Provider & model:** pick in the sidebar. Each provider ships a preset model list, plus an
  **✏️ Custom model…** option to type any model id the provider supports.

## 📝 License
MIT — free to use and modify.

---
**Built by Ibtasam Ahmad** | [LinkedIn](https://linkedin.com/in/ibtasam-ahmad) | [GitHub](https://github.com/Ibtasam-Ahmad)
