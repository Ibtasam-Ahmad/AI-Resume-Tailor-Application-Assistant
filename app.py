"""
AI Resume Tailor & Application Assistant
=======================================
A Streamlit app that tailors your resume and generates cover letters/emails
based on job descriptions or full job portal page text.

Features:
- Email Mode: Tailored Resume PDF + Cover Letter PDF + Email Subject/Body
- Job Portal Mode: Tailored Resume PDF + Cover Letter PDF + Q&A Answers
- One-click copy buttons for all text outputs
- Multiple Groq API key fallback support
- LaTeX to PDF compilation

Setup:
1. Install dependencies: pip install -r requirements.txt
2. Create .streamlit/secrets.toml with your Groq API keys
3. Ensure pdflatex is installed (TeX Live / MiKTeX)
4. Run: streamlit run app.py
"""

import streamlit as st
import os
import re
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple

# ── Third-party imports ──────────────────────────────────────────────────────
try:
    from groq import Groq
except ImportError:
    st.error("groq package not installed. Run: pip install groq")
    raise

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Resume Tailor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for copy buttons and styling ──────────────────────────────────
st.markdown("""
<style>
    .copy-box {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.5;
        border-left: 4px solid #1f77b4;
        position: relative;
    }
    .copy-btn {
        position: absolute;
        top: 8px;
        right: 8px;
        background: #1f77b4;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 4px 12px;
        font-size: 12px;
        cursor: pointer;
        z-index: 10;
    }
    .copy-btn:hover {
        background: #145a8c;
    }
    .section-header {
        color: #1f77b4;
        font-weight: 600;
        font-size: 18px;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .mode-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }
    .output-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    .stTextArea textarea {
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════════════
#  BASE RESUME & COVER LETTER (HARDCODED — YOUR MASTER TEMPLATES)
# ═════════════════════════════════════════════════════════════════════════════

BASE_RESUME_LATEX = r"""\documentclass[a4paper,10pt]{article}

\usepackage[left=0.7in,top=0.7in,right=0.7in,bottom=0.7in]{geometry}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{titlesec}
\usepackage{tabularx}
\usepackage{xcolor}
\usepackage{array}

% --- Professional dark blue for links ---
\definecolor{profblue}{RGB}{0, 51, 102}
\hypersetup{colorlinks=true, urlcolor=profblue, linkcolor=profblue}

% --- Section formatting: bold, large, subtle bottom rule ---
\titleformat{\section}{\large\bfseries\color{black}}{}{0em}{}[\vspace{-2pt}\textcolor{black!40}{\rule{\textwidth}{0.4pt}}]
\titlespacing{\section}{0pt}{10pt}{6pt}

% --- Consistent list spacing ---
\setlist[itemize]{leftmargin=1.5em, noitemsep, topsep=2pt, parsep=0pt}
\setlist[enumerate]{leftmargin=1.5em, noitemsep, topsep=2pt, parsep=0pt}

\begin{document}

% --- HEADER ---
\begin{center}
    {\LARGE \textbf{Ibtasam Ahmad}}\\[4pt]
    \vspace{3pt}
    \textbf{AI/ML Engineer}: Production RAG \& Multi-Agent Systems: Open to Relocation\\[2pt]
    +92 315 0180953 \hspace{0.5em} \hspace{0.5em} Lahore, Pakistan \\[3pt]
    \href{mailto:shibtasam@gmail.com}{shibtasam@gmail.com} \quad \quad
    \href{https://www.linkedin.com/in/ibtasam-ahmad}{linkedin.com/in/ibtasam-ahmad} \quad \quad
    \href{https://github.com/Ibtasam-Ahmad}{github.com/Ibtasam-Ahmad}
\end{center}

% --- PROFESSIONAL SUMMARY ---
\section*{Professional Summary}
Applied AI Engineer with \textbf{4+ years} of experience designing production-grade LLM systems, RAG architectures, autonomous AI agents, and scalable AI SaaS products. Specialized in Large language models, vector search, multi-agent orchestration (LangGraph/LangChain), and fine-tuning open-source models (LLaMA, GPT). Skilled in \textbf{LangGraph, LangChain, OpenAI, Claude, Gemini, Llama, Pinecone, Weaviate, LangSmith, AWS, Docker, and Open Source Models}. Proven track record of delivering enterprise AI solutions that automate workflows and reduce manual effort by \textbf{60--70\%}. Published researcher (LSTM vs QLSTM, arXiv 2024). \textbf{Actively seeking opportunities in Middle East, and Schengen countries. Available for immediate relocation.}

\section*{Core Technologies}
\noindent
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{5cm} X @{}}
\textbf{LLMs \& Models}          & GPT-4, Claude, Gemini, LLaMA (3.2), HuggingFace, OpenAI API, Groq \\
\textbf{AI Frameworks}           & LangChain, LangGraph, LangSmith, AbacusAI, AutoGen, LlamaIndex \\
\textbf{Vector Search}           & FAISS, Pinecone, Chroma, Weaviate, Hybrid Search, PgVector \\
\textbf{Agents \& Orchestration} & Multi-Agent Systems, LangGraph workflows, persistent memory, task routing \\
\textbf{Backend \& APIs}         & Python, FastAPI, Django, Flask, Django REST, RESTful APIs, WebSockets \\
\textbf{Cloud \& DevOps}         & AWS (EC2, S3, Lambda), GCP (Vertex AI, Cloud Run), Docker, CI/CD \\
\textbf{Computer Vision}         & YOLO, OCR, Tesseract, Image Processing \\
\textbf{Databases}               & PostgreSQL, MongoDB, BigQuery, SQL, Redis \\
\textbf{Other}                   & Twilio API, Vapi, Whisper, ffmpeg, Scrapy, Selenium \\
\end{tabularx}

% --- PROFESSIONAL EXPERIENCE ---
\section*{Professional Experience}

\textbf{Senior AI/ML Engineer} \hfill Nov 2025 -- Present\\
\textit{Visnext Software Solutions, Lahore, Pakistan}
\begin{itemize}
    \item Architected enterprise RAG pipelines with LLaMA 3.2 fine-tuning (Unsloth) and vector indexing (FAISS/Chroma), \textbf{reducing manual reporting by 60\%} for 5+ enterprise clients
    \item Developed multi-agent AI architectures for autonomous reasoning and task execution across complex workflows
    \item Built production chatbots/voicebots handling \textbf{5,000+ monthly conversations} (Twilio, Vapi integration)
    \item Automated property insights using BigQuery + Gemini, \textbf{cutting analysis turnaround time by 40\%}
\end{itemize}

\vspace{4pt}

\textbf{Python / AI Developer} \hfill May 2025 -- Nov 2025\\
\textit{Infolyze Solutions, Lahore, Pakistan}
\begin{itemize}
    \item Architected end-to-end AI pipelines using data ingestion, LLM fine-tuning (LLaMA 3.2/Unsloth), and vector indexing (FAISS, Chroma) for enterprise knowledge systems
    \item Built RAG-driven report generation and contextual chatbot products supporting enterprise document Q\&A and summarization workflows
    \item Deployed production-ready chatbots and voicebots (Twilio) integrated with APIs and databases
    \item Built multiple AI SaaS tools (resume analyzer, OCR automation, translators) contributing to new revenue streams
\end{itemize}

\vspace{4pt}

\textbf{AI Developer} \hfill Mar 2024 -- May 2025\\
\textit{DigiMark Developers, Lahore, Pakistan}
\begin{itemize}
    \item Delivered RAG-driven chatbots and voicebots using OpenAI, Claude, and HuggingFace models in live production
    \item Designed and deployed scalable APIs using Django REST, Flask, and FastAPI
    \item Built hybrid search solutions using SQL + vector databases (Pinecone, FAISS, Chroma) increasing retrieval precision
\end{itemize}

\vspace{4pt}

\textbf{Junior Python / AI Developer} \hfill Aug 2023 -- Mar 2024\\
\textit{Expert System Solution, Lahore, Pakistan}
\begin{itemize}
    \item Built AI solutions for NLP, OCR, and CV tasks using PyTorch, Keras, and scikit-learn
    \item Delivered LSTM-based prediction tools and OCR systems automating manual data processing for SMEs
\end{itemize}

% --- SELECTED PROJECTS ---
\section*{Projects}

\begin{itemize}[leftmargin=0pt, label={}]
    \item \textbf{CrossGroveAI (Insurance)}: FastAPI, MongoDB, Gemini AI, Groq, AWS S3, Docker \\
    Multi-tenant AI orchestrator automating insurance renewal, negotiation, and quotation workflows using hybrid LLM+OCR with state-machine tracking.

    \item \textbf{PixadentAI (Healthcare)}: FastAPI, PostgreSQL, AWS Transcribe Medical, Whisper, Claude API, Docker \\
    Clinical audio AI converting dental recordings to structured clinical notes with real-time cost analytics by tenant.

    \item \textbf{RippleAI (Crisis Prevention)}: FastAPI, LangGraph, WeaviateDB, OpenAI GPT-4, Claude \\
    Suicide prevention platform with trigger detection, intent classification, and crisis routing using multi-agent orchestration.

    \item \textbf{Adelphi Stock Brokers (Fintech)}: React, Next.js, FastAPI, TensorFlow, LSTM, FinGPT, LangChain, AWS \\
    Hybrid predictive models (Random Forest, LSTM, BiLSTM) improving stock prediction accuracy by 6--12\%.

    \item \textbf{Agent Analysis System}: AbacusAI, LLMs, Python \\
    Multi-agent AI report generation platform; \textbf{reduced manual analysis time by 70\%}.

    \item \textbf{Laila App}: FastAPI, Search Algorithms \\
    Multilingual khutba translation API with real-time Quranic search - \textbf{relevant for GCC markets}.

    \item \textbf{Pen Testing Agent Platform}: PostgreSQL, FastAPI, LangChain, OpenAI \\
    Automated vulnerability assessment, reducing manual analysis cycles by 50\%.

    \item \textbf{Permit Signal Insights}: BigQuery, Gemini, Python \\
    AI system parsing property/permit data to generate insights, \textbf{reducing research time by 50\%}.
\end{itemize}

% --- ADDITIONAL PROJECTS ---
\section*{Additional Projects}
\noindent
\textbf{AI/ML:} Chat-Bot \& Voice-Bot Web/Call App, CRE AI Tutor, Resume Analyzer (OCR+NLP+Vector DB), Chef Chatbot, Construction Chatbot, Sketch-This App, PDF-Based Custom Chatbot, Chat with CSV, Time Series Forecasting Suite (ARIMA/SARIMA/Prophet), Neural \& Quantum Neural Predictions (LSTM/QLSTM), Sentiment + Metaphor Detection. \\
\textbf{Computer Vision:} Wrong Parking Detection (YOLO), PPE Detection (YOLO), Screenshot Classification System. \\
\textbf{Data \& Automation:} Ebay Monitoring System (Time Series Forecasting), Scraper and Analytics Dashboard (BeautifulSoup, Scrapy, Pandas), Creator Ranking System (LSTM, Random Forest, NLP).

% --- EDUCATION ---
\section*{Education}

\textbf{BS (Honors) Computational Physics} \hfill Oct 2019 -- Jul 2023\\
\textit{University of the Punjab (CHEP), Lahore}\\
Thesis: \textit{Prediction of Stock Exchange Data Using LSTM \& QLSTM} (Published on arXiv)

\vspace{4pt}

\textbf{Diploma in Artificial Intelligence} \hfill Jan 2022 -- Oct 2022\\
\textit{University of the Punjab (NAVTTAC), Lahore}\\
FYP: Personal Protection Equipment Detection (YOLO)

% --- PUBLICATIONS ---
\section*{Publications}
\begin{itemize}[leftmargin=1.5em]
    \item Mahmood, T., \textbf{Ahmad, I.}, Ansar, M. M. Z., Darwish, J. A. \& Sherwani, R. A. K. (2024). \textit{Comparative Study of Long Short-Term Memory (LSTM) and Quantum Long Short-Term Memory (QLSTM): Prediction of Stock Market Movement.} arXiv:2409.08297. \\
    \href{https://doi.org/10.48550/arXiv.2409.08297}{https://doi.org/10.48550/arXiv.2409.08297}
\end{itemize}

% --- CERTIFICATIONS ---
\section*{Certifications}
\begin{itemize}[leftmargin=1.5em, itemsep=2pt]
    \item \href{https://www.credly.com/badges/4e9dd2d7-6323-4b65-87b6-b3330d6ce85f}{Meta Full-Stack Engineer Certificate}
    \item \href{https://www.credly.com/badges/7a8f02af-381b-4ee2-bd2e-7c9e1eccdbc4}{IBM AI Engineering Professional Certificate (V2)}
    \item \href{https://www.credly.com/badges/d27ef1d3-5843-40c4-a823-457c0178a169}{IBM Data Science Professional Certificate}
    \item \href{https://www.coursera.org/account/accomplishments/specialization/K6KMCT7Y62BY}{Machine Learning Specialization (Stanford/DeepLearning.AI)}
    \item \href{https://www.credly.com/badges/5af24d9b-5794-436e-add3-4ae1cefd6ec5}{Microsoft Certified: Azure AI Fundamentals}
    \item National Vocational and Technical Training Commission -- Artificial Intelligence
\end{itemize}

% --- LANGUAGES & RELOCATION ---
\section*{Languages \& Relocation}
\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{3cm} X @{}}
\textbf{English} & Professional Working Proficiency (written \& spoken) \\
\textbf{Urdu} & Native \\
\textbf{Arabic} & Basic Reading \\
\textbf{Relocation} & \textbf{Immediately available} for Middle East, and Schengen countries \\
\textbf{Visa Status} & Eligible for employer-sponsored work visa \\
\end{tabularx}

% --- LEADERSHIP & COMMUNITY ---
\section*{Leadership \& Community}
\begin{itemize}[leftmargin=1.5em]
    \item President -- CHEP Literary \& Event Societies
    \item IT Lead -- CHEP Scientific Society
    \item Associate Member -- Pakistan Nuclear Society
    \item In-charge -- PU Photography Club
    \item Active AI Writer on \href{https://medium.com/@shibtasam}{Medium}
    \item LinkedIn Creator (22,000+ followers) sharing AI insights
\end{itemize}

% --- CONFERENCES & COMPETITIONS ---
\section*{Conferences \& Competitions}
\begin{itemize}[leftmargin=1.5em]
    \item Connected Pakistan Conference 2022
    \item NASA Space Competition Pakistan 2022
    \item Future Fest Pakistan 2023, 2024, 2025
    \item Tech Conference by PITB (Punjab IT Board) 2022, 2023, 2024
    \item Startup Grind Lahore 2025
\end{itemize}

\end{document}"""

BASE_COVER_LETTER_LATEX = r"""\documentclass[10.7pt,a4paper]{article}

\usepackage[left=1in,top=1in,right=1in,bottom=1in]{geometry}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{parskip}

% --- Professional formatting ---
\definecolor{profblue}{RGB}{0, 51, 102}
\hypersetup{colorlinks=true, urlcolor=profblue, linkcolor=profblue}

\setlength{\parindent}{0pt}
\setlength{\parskip}{0.8em}

\begin{document}

% --- Sender Info (Top Right) ---
\begin{flushright}
\textbf{Ibtasam Ahmad}\\
AI/ML Engineer\\
Lahore, Pakistan\\
+92 315 0180953\\
\href{mailto:shibtasam@gmail.com}{shibtasam@gmail.com}\\
\href{https://www.linkedin.com/in/ibtasam-ahmad}{linkedin.com/in/ibtasam-ahmad}\\
\href{https://github.com/Ibtasam-Ahmad}{github.com/Ibtasam-Ahmad}
\end{flushright}

\vspace{0.5em}

\vspace{1em}

% --- Subject Line ---
\textbf{Re: Application for {JOB_TITLE}}

\vspace{0.5em}

% --- Salutation ---
Dear Hiring Manager,

% --- Opening Paragraph ---
I am writing to express my strong interest in the {JOB_TITLE} position. As an Applied AI Engineer with \textbf{4+ years} of hands-on experience designing production-grade LLM systems, RAG architectures, and autonomous multi-agent systems, I am eager to bring my expertise to your team. I am \textbf{immediately available for relocation} and fully prepared to contribute from day one.

% --- Body Paragraph 1: Core Expertise ---
My background aligns directly with the demands of modern AI engineering roles. At \textbf{Visnext Software Solutions}, I architected enterprise RAG pipelines using LLaMA 3.2 fine-tuning (Unsloth) and vector indexing (FAISS/Chroma), \textbf{reducing manual reporting by 60\%} for 5+ enterprise clients. I developed multi-agent AI architectures for autonomous reasoning and built production chatbots/voicebots handling \textbf{5,000+ monthly conversations} via Twilio and Vapi integration. Additionally, I automated property insights using BigQuery + Gemini, \textbf{cutting analysis turnaround time by 40\%}.

% --- Body Paragraph 2: Technical Breadth ---
My technical toolkit spans the full AI stack: \textbf{LangChain, LangGraph, LangSmith} for agent orchestration; \textbf{FAISS, Pinecone, Chroma, Weaviate} for vector search; and \textbf{FastAPI, Django, Flask} for backend API development. I have deployed solutions on \textbf{AWS (EC2, S3, Lambda)} and \textbf{GCP (Vertex AI, Cloud Run)}, containerized with Docker and automated via CI/CD. My project portfolio includes \textbf{RippleAI} (a suicide prevention platform with multi-agent crisis routing), and \textbf{CrossGroveAI} (a multi-tenant insurance orchestrator). These experiences have honed my ability to deliver scalable, high-impact AI products in fast-paced environments.

% --- Body Paragraph 3: Research and Continuous Growth ---
Beyond production engineering, I am a \textbf{published researcher} (arXiv 2024: arXiv.2409.08297) on LSTM vs QLSTM for stock market prediction, and I hold certifications from \textbf{Meta, IBM, Microsoft Azure, and Stanford/DeepLearning.AI}. I actively share AI articles on Medium and insights with \textbf{22,000+ LinkedIn followers} and contribute to the community through conferences like Future Fest Pakistan and the Punjab IT Board Tech Conference. This blend of research rigor, production excellence, and community engagement positions me to drive innovation.

% --- Body Paragraph 4: Relocation and Availability ---
I am \textbf{fully committed to relocating immediately} and have researched the tech ecosystems, visa pathways, and professional landscapes of your region. I am eligible for employer-sponsored work visas. My adaptability, combined with a proven track record of reducing manual workloads by \textbf{60--70\%} across enterprise clients, ensures I will deliver measurable value swiftly.

% --- Closing Paragraph ---
I would welcome the opportunity to discuss how my expertise in production RAG, multi-agent systems, and scalable AI SaaS can contribute to your Company's goals. Thank you for considering my application. I look forward to the possibility of speaking with you.

\vspace{1em}

% --- Sign-off ---
Sincerely,\\[1.5em]
\textbf{Ibtasam Ahmad}

\end{document}"""


# ═════════════════════════════════════════════════════════════════════════════
#  GROQ API CLIENT WITH MULTI-KEY FALLBACK
# ═════════════════════════════════════════════════════════════════════════════

class GroqClientManager:
    """Manages multiple Groq API keys with automatic failover."""

    def __init__(self):
        self.keys: List[str] = []
        self.current_index: int = 0
        self._load_keys()

    def _load_keys(self) -> None:
        """Load API keys from Streamlit secrets.toml."""
        # Try multiple naming conventions
        possible_keys = []

        # Pattern 1: GROQ_API_KEY_1, GROQ_API_KEY_2, ...
        for i in range(1, 20):
            key_name = f"GROQ_API_KEY_{i}"
            if key_name in st.secrets:
                possible_keys.append(st.secrets[key_name])

        # Pattern 2: groq_api_key_1, groq_api_key_2, ...
        for i in range(1, 20):
            key_name = f"groq_api_key_{i}"
            if key_name in st.secrets:
                possible_keys.append(st.secrets[key_name])

        # Pattern 3: Single key
        if "GROQ_API_KEY" in st.secrets:
            possible_keys.append(st.secrets["GROQ_API_KEY"])
        if "groq_api_key" in st.secrets:
            possible_keys.append(st.secrets["groq_api_key"])

        # Pattern 4: List of keys
        if "GROQ_API_KEYS" in st.secrets:
            val = st.secrets["GROQ_API_KEYS"]
            if isinstance(val, list):
                possible_keys.extend(val)
            elif isinstance(val, str):
                possible_keys.extend([k.strip() for k in val.split(",") if k.strip()])

        # Deduplicate while preserving order
        seen = set()
        for k in possible_keys:
            if k and k not in seen:
                seen.add(k)
                self.keys.append(k)

        if not self.keys:
            st.error("""
❌ **No Groq API keys found!**

Please add your API keys to `.streamlit/secrets.toml` like this:

```toml
GROQ_API_KEY_1 = "gsk_xxxxxxxxxxxxxxxxxxxxxxxx"
GROQ_API_KEY_2 = "gsk_yyyyyyyyyyyyyyyyyyyyyyyy"
GROQ_API_KEY_3 = "gsk_zzzzzzzzzzzzzzzzzzzzzzzz"
```
            """)
            st.stop()

        st.sidebar.success(f"✅ Loaded {len(self.keys)} Groq API key(s)")

    def get_client(self) -> Groq:
        """Get a Groq client using the current key."""
        if self.current_index >= len(self.keys):
            self.current_index = 0  # Reset and try again
        return Groq(api_key=self.keys[self.current_index])

    def rotate_key(self) -> None:
        """Move to the next API key."""
        self.current_index = (self.current_index + 1) % len(self.keys)

    def call_with_fallback(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.3,
        max_tokens: int = 8000,
        response_format: Optional[Dict] = None,
    ) -> str:
        """Call Groq API with automatic key rotation on failure."""
        attempts = 0
        max_attempts = len(self.keys)
        last_error = None

        while attempts < max_attempts:
            try:
                client = self.get_client()
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format

                response = client.chat.completions.create(**kwargs)
                return response.choices[0].message.content

            except Exception as e:
                last_error = str(e)
                attempts += 1
                self.rotate_key()
                st.sidebar.warning(f"⚠️ Key {attempts} failed, rotating... ({last_error[:80]})")

        raise RuntimeError(f"All {len(self.keys)} API keys failed. Last error: {last_error}")


# ═════════════════════════════════════════════════════════════════════════════
#  LATEX → PDF COMPILATION
# ═════════════════════════════════════════════════════════════════════════════

def compile_latex_to_pdf(latex_content: str, output_filename: str = "output") -> Optional[bytes]:
    """
    Compile LaTeX content to PDF using pdflatex.
    Returns PDF bytes or None if compilation fails.
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, f"{output_filename}.tex")

        # Write LaTeX to file
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)

        # Try pdflatex compilation
        try:
            # Run pdflatex twice for references
            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, tex_path],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

            pdf_path = os.path.join(tmpdir, f"{output_filename}.pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    return f.read()
            else:
                st.warning("⚠️ pdflatex did not produce PDF. Check if TeX Live/MiKTeX is installed.")
                return None

        except FileNotFoundError:
            st.error("""
❌ **pdflatex not found!**

To generate PDFs, you need a LaTeX distribution installed:

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended
```

**macOS:**
```bash
brew install --cask mactex
```

**Windows:**
Download and install MiKTeX from https://miktex.org/download

**Or use the fallback:** The app will still show you the LaTeX code to copy and compile manually.
            """)
            return None
        except subprocess.TimeoutExpired:
            st.error("⏱️ LaTeX compilation timed out.")
            return None
        except Exception as e:
            st.error(f"❌ LaTeX compilation error: {e}")
            return None


# ═════════════════════════════════════════════════════════════════════════════
#  COPY-TO-CLIPBOARD HELPER
# ═════════════════════════════════════════════════════════════════════════════

def copyable_text(label: str, text: str, key_suffix: str = "") -> None:
    """Display text with a one-click copy button using Streamlit's native copy feature."""
    col1, col2 = st.columns([0.92, 0.08])

    with col1:
        st.code(text, language="text")

    with col2:
        # Use st_copy_to_clipboard if available, otherwise use a download button workaround
        try:
            import streamlit_copy_to_clipboard as stcp
            stcp.copy_to_clipboard(text, key=f"copy_{key_suffix}_{hash(text) & 0xFFFFFF}")
        except ImportError:
            # Fallback: download as text file
            st.download_button(
                label="📋",
                data=text,
                file_name=f"{label.lower().replace(' ', '_')}.txt",
                mime="text/plain",
                key=f"dl_{key_suffix}_{hash(text) & 0xFFFFFF}",
                help=f"Download {label} as text file",
            )


def copyable_latex(label: str, latex_code: str, key_suffix: str = "") -> None:
    """Display LaTeX code with copy button and expander."""
    with st.expander(f"📄 {label} — Click to view LaTeX source", expanded=False):
        col1, col2 = st.columns([0.92, 0.08])
        with col1:
            st.code(latex_code, language="latex")
        with col2:
            try:
                import streamlit_copy_to_clipboard as stcp
                stcp.copy_to_clipboard(latex_code, key=f"copy_latex_{key_suffix}_{hash(latex_code) & 0xFFFFFF}")
            except ImportError:
                st.download_button(
                    label="📋",
                    data=latex_code,
                    file_name=f"{label.lower().replace(' ', '_')}.tex",
                    mime="text/x-tex",
                    key=f"dl_latex_{key_suffix}_{hash(latex_code) & 0xFFFFFF}",
                    help=f"Download {label} LaTeX source",
                )


# ═════════════════════════════════════════════════════════════════════════════
#  PROMPT ENGINEERING
# ═════════════════════════════════════════════════════════════════════════════

def build_resume_tailor_prompt(base_resume: str, job_text: str, mode: str) -> str:
    """Build the prompt for tailoring the resume."""
    return f"""You are an expert resume writer and ATS optimization specialist.

TASK: Tailor the following resume to match the job description/portal text provided.

RULES:
1. Keep the EXACT same LaTeX structure, document class, packages, and formatting
2. Modify ONLY the content to highlight skills and experience most relevant to the job
3. Add job-specific keywords naturally into the Professional Summary and bullet points
4. Reorder projects to prioritize those most relevant to the job
5. Adjust the Professional Summary to directly address the job requirements
6. Keep all hyperlinks, formatting commands, and LaTeX syntax intact
7. Do NOT add comments or explanations outside the LaTeX code
8. Ensure the output is valid, compilable LaTeX

MODE: {mode}

BASE RESUME (LaTeX):
```latex
{base_resume}
```

JOB TEXT:
```
{job_text}
```

OUTPUT: Return ONLY the complete tailored LaTeX resume code. No markdown code fences, no explanations.
"""


def build_cover_letter_prompt(base_cover_letter: str, job_text: str, job_title: str, mode: str) -> str:
    """Build the prompt for tailoring the cover letter."""
    return f"""You are an expert cover letter writer for tech professionals.

TASK: Tailor the following cover letter to match the job description/portal text provided.

RULES:
1. Keep the EXACT same LaTeX structure, document class, packages, and formatting
2. Replace {{JOB_TITLE}} with the actual job title extracted from the job text
3. Customize the opening paragraph to mention the specific company and role
4. Highlight 2-3 most relevant projects/experiences that match the job requirements
5. Adjust technical details to align with the job's tech stack
6. Keep all hyperlinks, formatting commands, and LaTeX syntax intact
7. Do NOT add comments or explanations outside the LaTeX code
8. Ensure the output is valid, compilable LaTeX

MODE: {mode}

BASE COVER LETTER (LaTeX):
```latex
{base_cover_letter}
```

JOB TEXT:
```
{job_text}
```

EXTRACTED JOB TITLE: {job_title}

OUTPUT: Return ONLY the complete tailored LaTeX cover letter code. No markdown code fences, no explanations.
"""


def build_email_prompt(job_text: str, job_title: str) -> str:
    """Build the prompt for generating email subject and body."""
    return f"""You are an expert job application email writer.

TASK: Write a professional cold email for a job application.

CONTEXT:
- Applicant: Ibtasam Ahmad, AI/ML Engineer with 4+ years experience
- Specialties: LLM systems, RAG architectures, multi-agent systems, LangChain/LangGraph
- Open to relocation (Middle East, Schengen)
- Email: shibtasam@gmail.com
- LinkedIn: linkedin.com/in/ibtasam-ahmad
- GitHub: github.com/Ibtasam-Ahmad

JOB TEXT:
```
{job_text}
```

EXTRACTED JOB TITLE: {job_title}

RULES:
1. Subject line should be concise, professional, and mention the role
2. Email body should be 3-4 short paragraphs
3. Mention that resume and cover letter are attached as PDFs
4. Show enthusiasm without being overly casual
5. Include a clear call-to-action (request for interview/call)
6. Keep total email under 200 words

OUTPUT FORMAT (JSON):
{{
    "email_subject": "...",
    "email_body": "..."
}}
"""


def build_portal_qa_prompt(job_text: str, base_resume_text: str) -> str:
    """Build the prompt for extracting and answering job portal questions."""
    return f"""You are an expert job application assistant.

TASK: Analyze the job portal page text and extract all application questions. Then provide tailored answers based on the applicant's resume.

APPLICANT RESUME SUMMARY:
{base_resume_text}

JOB PORTAL PAGE TEXT:
```
{job_text}
```

RULES:
1. Extract ALL questions, fields, and prompts from the portal text
2. This includes: text questions, dropdown options, checkbox items, salary expectations, start date, etc.
3. Provide concise, professional answers (2-4 sentences each)
4. Tailor each answer to highlight relevant experience from the resume
5. For salary questions, give a reasonable range based on the role and region
6. For "Why this company?" questions, research-style answers based on the job text
7. For "Availability" questions, state "Immediately available for relocation"

OUTPUT FORMAT (JSON):
{{
    "questions": [
        {{
            "question": "exact question text from portal",
            "answer": "tailored answer"
        }},
        ...
    ]
}}

If no explicit questions are found, generate common questions based on the job description and provide answers.
"""


# ═════════════════════════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

def extract_job_title(job_text: str) -> str:
    """Extract job title from job text using simple heuristics."""
    lines = job_text.strip().split("\n")
    # Try first non-empty line
    for line in lines[:10]:
        line = line.strip()
        if line and len(line) < 100:
            # Common patterns
            if any(kw in line.lower() for kw in ["engineer", "developer", "scientist", "manager", "lead", "architect", "analyst", "consultant", "specialist"]):
                return line
    # Fallback: use first line
    return lines[0].strip() if lines else "the Position"


def clean_latex_output(raw: str) -> str:
    """Clean LLM output to extract pure LaTeX code."""
    # Remove markdown code fences
    raw = re.sub(r"```latex\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"```\s*$", "", raw)
    raw = re.sub(r"^```\s*", "", raw)
    # Remove any leading/trailing whitespace
    raw = raw.strip()
    # Ensure it starts with \documentclass
    if "\\documentclass" not in raw:
        # Try to find it
        match = re.search(r"(\\documentclass.*)", raw, re.DOTALL)
        if match:
            raw = match.group(1)
    return raw


# ═════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION
# ═════════════════════════════════════════════════════════════════════════════

def main():
    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.title("⚙️ Settings")
        st.markdown("---")

        # Model selection
        model = st.selectbox(
            "Groq Model",
            [
                "llama-3.3-70b-versatile",
                "llama-3.1-70b-versatile",
                "llama-3.1-8b-instant",
                "mixtral-8x7b-32768",
                "gemma2-9b-it",
            ],
            index=0,
            help="Select the LLM model to use for generation",
        )

        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Lower = more factual/conservative, Higher = more creative",
        )

        st.markdown("---")
        st.markdown("### 📋 Instructions")
        st.markdown("""
1. Select **Email** or **Job Portal** mode
2. Paste the job description or full portal page text
3. Click **Generate**
4. Download PDFs and copy text outputs
        """)

        st.markdown("---")
        st.markdown("### 🔑 API Keys")
        # Initialize manager to show key count
        if "groq_manager" not in st.session_state:
            try:
                st.session_state.groq_manager = GroqClientManager()
            except:
                pass

    # ── Header ───────────────────────────────────────────────────────────────
    st.title("📄 AI Resume Tailor & Application Assistant")
    st.markdown("Tailor your resume, generate cover letters, and craft perfect job applications with AI.")
    st.markdown("---")

    # ── Mode Selection ───────────────────────────────────────────────────────
    mode = st.radio(
        "Select Application Mode:",
        ["📧 Email Application", "🌐 Job Portal Application"],
        horizontal=True,
        help="Email mode generates email subject/body. Portal mode extracts and answers portal questions.",
    )
    mode_value = "email" if "Email" in mode else "portal"

    # ── Job Text Input ───────────────────────────────────────────────────────
    st.markdown("### 📝 Paste Job Text")
    job_text = st.text_area(
        label="Job Description or Portal Page Text",
        placeholder="Paste the complete job description here...\\n\\nFor Job Portal mode, paste the ENTIRE page text including all questions, fields, and requirements.",
        height=300,
        help="For best results, include the full job description with requirements, responsibilities, and company info.",
    )

    # ── Generate Button ──────────────────────────────────────────────────────
    generate_col, _ = st.columns([0.2, 0.8])
    with generate_col:
        generate_clicked = st.button("✨ Generate Application Materials", type="primary", use_container_width=True)

    # ── Processing ─────────────────────────────────────────────────────────
    if generate_clicked:
        if not job_text.strip():
            st.error("❌ Please paste the job text first!")
            st.stop()

        # Initialize Groq manager
        try:
            groq_manager = GroqClientManager()
        except Exception as e:
            st.error(f"Failed to initialize Groq client: {e}")
            st.stop()

        # Extract job title
        job_title = extract_job_title(job_text)
        st.info(f"📌 Detected Job Title: **{job_title}**")

        # Create progress containers
        progress_bar = st.progress(0)
        status_text = st.empty()

        results = {}

        # ── Step 1: Tailor Resume ──────────────────────────────────────────
        status_text.text("📝 Step 1/4: Tailoring resume to job description...")
        progress_bar.progress(15)

        try:
            resume_prompt = build_resume_tailor_prompt(BASE_RESUME_LATEX, job_text, mode_value)
            tailored_resume_raw = groq_manager.call_with_fallback(
                messages=[{"role": "user", "content": resume_prompt}],
                model=model,
                temperature=temperature,
                max_tokens=8000,
            )
            tailored_resume = clean_latex_output(tailored_resume_raw)
            results["tailored_resume_latex"] = tailored_resume
        except Exception as e:
            st.error(f"❌ Resume tailoring failed: {e}")
            st.stop()

        # ── Step 2: Tailor Cover Letter ────────────────────────────────────
        status_text.text("📝 Step 2/4: Generating tailored cover letter...")
        progress_bar.progress(35)

        try:
            cover_prompt = build_cover_letter_prompt(BASE_COVER_LETTER_LATEX, job_text, job_title, mode_value)
            tailored_cover_raw = groq_manager.call_with_fallback(
                messages=[{"role": "user", "content": cover_prompt}],
                model=model,
                temperature=temperature,
                max_tokens=8000,
            )
            tailored_cover = clean_latex_output(tailored_cover_raw)
            results["tailored_cover_latex"] = tailored_cover
        except Exception as e:
            st.error(f"❌ Cover letter generation failed: {e}")
            st.stop()

        # ── Step 3: Mode-specific content ──────────────────────────────────
        if mode_value == "email":
            status_text.text("📧 Step 3/4: Generating email subject and body...")
            progress_bar.progress(55)

            try:
                email_prompt = build_email_prompt(job_text, job_title)
                email_raw = groq_manager.call_with_fallback(
                    messages=[{"role": "user", "content": email_prompt}],
                    model=model,
                    temperature=temperature,
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
                email_data = json.loads(email_raw)
                results["email_subject"] = email_data.get("email_subject", "")
                results["email_body"] = email_data.get("email_body", "")
            except Exception as e:
                st.error(f"❌ Email generation failed: {e}")
                results["email_subject"] = f"Application for {job_title} — Ibtasam Ahmad"
                results["email_body"] = "Email generation failed. Please compose manually."

        else:  # portal mode
            status_text.text("🌐 Step 3/4: Analyzing portal questions and generating answers...")
            progress_bar.progress(55)

            try:
                # Create a text summary of resume for the QA prompt
                resume_summary = """Ibtasam Ahmad — AI/ML Engineer, 4+ years experience.
Specialties: LLM systems, RAG architectures, multi-agent systems (LangGraph/LangChain),
vector search (Pinecone, FAISS, Chroma, Weaviate), fine-tuning (LLaMA 3.2, Unsloth),
backend APIs (FastAPI, Django, Flask), cloud deployment (AWS, GCP, Docker).
Key projects: CrossGroveAI (insurance), PixadentAI (healthcare), RippleAI (crisis prevention),
Adelphi Stock Brokers (fintech). Published researcher (LSTM vs QLSTM, arXiv 2024).
Certifications: Meta, IBM, Microsoft Azure, Stanford/DeepLearning.AI.
Open to relocation (Middle East, Schengen). Immediately available."""

                qa_prompt = build_portal_qa_prompt(job_text, resume_summary)
                qa_raw = groq_manager.call_with_fallback(
                    messages=[{"role": "user", "content": qa_prompt}],
                    model=model,
                    temperature=temperature,
                    max_tokens=4000,
                    response_format={"type": "json_object"},
                )
                qa_data = json.loads(qa_raw)
                results["questions_answers"] = qa_data.get("questions", [])
            except Exception as e:
                st.error(f"❌ Q&A generation failed: {e}")
                results["questions_answers"] = []

        # ── Step 4: Compile PDFs ───────────────────────────────────────────
        status_text.text("📄 Step 4/4: Compiling PDFs...")
        progress_bar.progress(75)

        # Compile Resume PDF
        resume_pdf_bytes = compile_latex_to_pdf(results["tailored_resume_latex"], "tailored_resume")
        results["resume_pdf"] = resume_pdf_bytes

        # Compile Cover Letter PDF
        cover_pdf_bytes = compile_latex_to_pdf(results["tailored_cover_latex"], "tailored_cover_letter")
        results["cover_pdf"] = cover_pdf_bytes

        progress_bar.progress(100)
        status_text.empty()
        st.success("✅ All materials generated successfully!")

        # ── Display Results ────────────────────────────────────────────────
        st.markdown("---")
        st.markdown("## 📦 Generated Materials")

        # PDF Downloads Row
        pdf_col1, pdf_col2, pdf_col3 = st.columns(3)

        with pdf_col1:
            st.markdown("<div class='output-card'>", unsafe_allow_html=True)
            st.markdown("### 📄 Tailored Resume")
            if results.get("resume_pdf"):
                st.download_button(
                    label="⬇️ Download Resume PDF",
                    data=results["resume_pdf"],
                    file_name=f"Ibtasam_Ahmad_Resume_{job_title.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.warning("PDF compilation failed. LaTeX source available below.")
            copyable_latex("Resume LaTeX", results["tailored_resume_latex"], "resume")
            st.markdown("</div>", unsafe_allow_html=True)

        with pdf_col2:
            st.markdown("<div class='output-card'>", unsafe_allow_html=True)
            st.markdown("### 📄 Cover Letter")
            if results.get("cover_pdf"):
                st.download_button(
                    label="⬇️ Download Cover Letter PDF",
                    data=results["cover_pdf"],
                    file_name=f"Ibtasam_Ahmad_Cover_Letter_{job_title.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.warning("PDF compilation failed. LaTeX source available below.")
            copyable_latex("Cover Letter LaTeX", results["tailored_cover_latex"], "cover")
            st.markdown("</div>", unsafe_allow_html=True)

        with pdf_col3:
            st.markdown("<div class='output-card'>", unsafe_allow_html=True)
            if mode_value == "email":
                st.markdown("### 📧 Email")
                st.markdown(f"**Subject:**")
                copyable_text("Email Subject", results["email_subject"], "email_subject")
                st.markdown(f"**Body:**")
                copyable_text("Email Body", results["email_body"], "email_body")
            else:
                st.markdown("### 🌐 Portal Q&A")
                st.info(f"Found {len(results.get('questions_answers', []))} questions")
            st.markdown("</div>", unsafe_allow_html=True)

        # ── Email Mode: Full Email Display ─────────────────────────────────
        if mode_value == "email":
            st.markdown("---")
            st.markdown("## 📧 Complete Email")

            with st.container():
                st.markdown("<div class='output-card'>", unsafe_allow_html=True)

                st.markdown("#### 📋 Email Subject")
                copyable_text("Subject", results["email_subject"], "email_subject_full")

                st.markdown("#### 📋 Email Body")
                copyable_text("Body", results["email_body"], "email_body_full")

                # Full combined email for easy copy
                full_email = f"Subject: {results['email_subject']}\n\n{results['email_body']}"
                st.markdown("#### 📋 Full Email (Subject + Body)")
                copyable_text("Full Email", full_email, "email_full")

                st.markdown("</div>", unsafe_allow_html=True)

        # ── Portal Mode: Q&A Display ─────────────────────────────────────
        else:
            st.markdown("---")
            st.markdown("## 🌐 Job Portal Questions & Answers")

            if results.get("questions_answers"):
                for i, qa in enumerate(results["questions_answers"]):
                    with st.container():
                        st.markdown("<div class='output-card'>", unsafe_allow_html=True)
                        st.markdown(f"**Q{i+1}:** {qa.get('question', 'N/A')}")
                        copyable_text(f"Answer {i+1}", qa.get('answer', 'N/A'), f"qa_{i}")
                        st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("No questions were detected. Try pasting more complete portal page text.")

        # ── Session Storage ──────────────────────────────────────────────
        st.session_state.last_results = results
        st.session_state.last_job_title = job_title

    # ── Footer ───────────────────────────────────────────────────────────────
    st.markdown("---")
    st.caption("Built with ❤️ using Streamlit + Groq AI | Ibtasam Ahmad")


if __name__ == "__main__":
    main()