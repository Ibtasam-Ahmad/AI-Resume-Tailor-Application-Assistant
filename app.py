"""
AI Resume Tailor & Application Assistant
=======================================
A Streamlit app that heavily tailors a fixed master resume + cover letter to a
specific job description, and generates a matching application email OR job-portal
Q&A answers — all reviewed and editable before the final PDF is built.

Key behaviors:
- Master resume & cover letter are HARDCODED below (Ibtasam Ahmad). No upload needed.
- Work-mode aware:  Onsite / Hybrid / Remote  + a Job Location field.
    * Remote           -> relocation language removed, remote capability emphasized.
    * Location = Lahore -> presented as a LOCAL candidate (no relocation).
    * Other location    -> "immediately available to relocate to <that city>".
- JD-centric tailoring: summary, skills, projects, bullets reorganized around the JD.
- Review -> Edit -> Approve gate: AI shows what changed in editable boxes; the PDF is
  compiled from YOUR (possibly edited) version only after you approve.
- Multiple Groq API keys with automatic failover on rate-limit / auth errors.

Setup:
1. pip install -r requirements.txt
2. Create .streamlit/secrets.toml with your Groq API key(s)
3. Install pdflatex (TeX Live / MiKTeX) for PDF output
4. streamlit run app.py
"""

import os
import re
import json
import subprocess
import tempfile
from typing import Optional, List, Dict, Tuple

import streamlit as st

# ── Page config MUST be the first Streamlit call ─────────────────────────────
st.set_page_config(
    page_title="AI Resume Tailor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Third-party imports ──────────────────────────────────────────────────────
try:
    from groq import Groq
except ImportError:
    st.error("`groq` package not installed. Run: pip install groq")
    raise


# ═════════════════════════════════════════════════════════════════════════════
#  MASTER RESUME & COVER LETTER  (HARDCODED — the app always uses these)
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
Applied AI Engineer with \textbf{4+ years} of experience designing production-grade LLM systems, RAG architectures, autonomous AI agents, and scalable AI SaaS products. Specialized in Large language models, vector search, multi-agent orchestration (LangGraph/LangChain), and fine-tuning open-source models (LLaMA, GPT).  Skilled in \textbf{LangGraph, LangChain, OpenAI, Claude, Gemini, Llama, Pinecone, Weaviate, LangSmith, AWS, Docker, and Open Source Models}. Proven track record of delivering enterprise AI solutions that automate workflows and reduce manual effort by \textbf{60--70\%}. Published researcher (LSTM vs QLSTM, arXiv 2024). \textbf{Actively seeking opportunities in Middle East, and Schengen countries. Available for immediate relocation.}

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

    \item \textbf{GuardianAI (Crisis Prevention)}: FastAPI, LangGraph, WeaviateDB, OpenAI GPT-4, Claude \\
    Suicide/Abuse prevention platform with trigger detection, intent classification, and crisis routing using multi-agent orchestration.

    \item \textbf{ForecastAI (Fintech)}: React, Next.js, FastAPI, TensorFlow, LSTM, Prophet, FinanceGPT, LangChain, AWS \\
    Hybrid predictive models (Random Forest, LSTM, ARIMA/SARIMA, Prophet) improving stock prediction accuracy by 6--12\%.

    \item \textbf{Agent Analysis System}: AbacusAI, LLMs, Python \\
    Multi-agent AI report generation platform; \textbf{reduced manual analysis time by 70\%}.

    \item \textbf{AI HR Flow Automation}: FastAPI, PostgreSQL, ElevenLabs, Google Calendar API, LLMs (GPT-4/Claude) \\
    End-to-end recruitment automation: job import, multi-LLM resume parsing \& scoring, AI voice interviews via ElevenLabs, Calling via Twillio, and automated interview scheduling with Google Calendar; \textbf{reduced recruitment cycle time by 50\%}.

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
AI/ML Engineer -- Production RAG \& Multi-Agent Systems\\
Lahore, Pakistan\\
+92 315 0180953\\
\href{mailto:shibtasam@gmail.com}{shibtasam@gmail.com}\\
\href{https://www.linkedin.com/in/ibtasam-ahmad}{linkedin.com/in/ibtasam-ahmad}\\
\href{https://github.com/Ibtasam-Ahmad}{github.com/Ibtasam-Ahmad}
\end{flushright}

\vspace{0.5em}

\vspace{0.5em}

% --- Subject Line ---
\textbf{Re: Application for AI/ML Engineer Position}

\vspace{0.5em}

% --- Salutation ---
Dear Hiring Manager,

% --- Opening Paragraph ---
I am writing to apply for the AI/ML Engineer position at your organization. With \textbf{4+ years} of experience designing production-grade LLM systems, RAG architectures, and autonomous multi-agent systems, I am confident in my ability to deliver impactful AI solutions for your team. I am \textbf{immediately available for relocation} to the Middle East, Schengen countries, or any global tech hub.

% --- Body Paragraph 1: RAG and Production Experience ---
My expertise centers on building enterprise-grade RAG pipelines and AI agents that drive measurable business outcomes. At \textbf{Visnext Software Solutions}, I architected RAG systems using LLaMA 3.2 fine-tuning (Unsloth) and vector indexing with FAISS/Chroma, \textbf{reducing manual reporting efforts by 60\%} across 5+ enterprise clients. I developed multi-agent architectures using LangGraph for autonomous reasoning and complex workflow execution, and deployed production chatbots/voicebots handling \textbf{5,000+ monthly conversations} via Twilio and Vapi. I also built an end-to-end \textbf{AI HR Flow Automation} platform that imports job listings, parses and scores resumes using multi-provider LLMs, conducts AI-powered voice interviews via ElevenLabs, and automates interview scheduling through Google Calendar \textbf{reducing recruitment cycle time by 50\%}. At \textbf{Infolyze Solutions}, I built end-to-end AI pipelines and SaaS tools---including resume analyzers and OCR automation---that opened new revenue streams and automated document Q\&A workflows.

% --- Body Paragraph 2: Full-Stack AI Engineering ---
My technical stack is comprehensive and production-ready: \textbf{LangChain, LangGraph, and LangSmith} for agent orchestration; \textbf{FAISS, Pinecone, Chroma, Weaviate, and hybrid search} for vector retrieval; and \textbf{FastAPI, Django, and Flask} for scalable API development. I deploy on \textbf{AWS (EC2, S3, Lambda)} and \textbf{GCP (Vertex AI, Cloud Run)}, with Docker and CI/CD ensuring reliable delivery. Notable projects include \textbf{GuardianAI}---a crisis prevention platform using multi-agent orchestration for trigger detection and crisis routing; \textbf{CrossGroveAI}, an insurance orchestrator automating renewal, negotiation, and quotation workflows with hybrid LLM+OCR; and \textbf{ForecastAI}, a fintech platform improving stock prediction accuracy by 6--12\% using hybrid models (LSTM, Random Forest, Prophet). These experiences demonstrate my ability to architect, build, and scale complex AI products from concept to production.

% --- Body Paragraph 3: Research and Community Engagement ---
Beyond engineering, I maintain a strong research orientation. I am a \textbf{published author} (arXiv 2024: Comparative Study of LSTM and QLSTM for Stock Market Prediction) and hold professional certifications from \textbf{Meta, IBM, Microsoft Azure, and Stanford/DeepLearning.AI}. I actively contribute to the AI community through technical articles on Medium and insights shared with my \textbf{22,000+ LinkedIn followers}. I have participated in major industry conferences including Future Fest Pakistan and PITB Tech Conferences, staying at the forefront of AI innovation.

% --- Body Paragraph 4: Relocation and Commitment ---
I am \textbf{fully prepared for immediate relocation} and have proactively researched visa pathways and the professional landscape of target regions. My adaptability, combined with a track record of \textbf{reducing manual workloads by 60--70\%} across multiple enterprise implementations, ensures I will deliver value from day one.

% --- Closing Paragraph ---
I would welcome the opportunity to discuss how my experience in production RAG, multi-agent orchestration, and scalable AI SaaS aligns with your organization's goals. Thank you for your time and consideration---I look forward to the possibility of contributing to your team.

\vspace{1em}

% --- Sign-off ---
Sincerely,\\[1.5em]
\textbf{Ibtasam Ahmad}

\end{document}"""


# Candidate home base — used to decide when relocation language is needed.
HOME_CITY = "Lahore"
HOME_COUNTRY = "Pakistan"

# Marker the model appends after the LaTeX so we can split doc from changelog.
CHANGE_MARKER = "===CHANGES==="


# ═════════════════════════════════════════════════════════════════════════════
#  PERSONAL DETAILS  (scraped once from the master resume)
# ═════════════════════════════════════════════════════════════════════════════

def extract_personal_details(resume_tex: str) -> Dict[str, str]:
    details: Dict[str, str] = {}

    name_match = re.search(r"\\LARGE\s*\\textbf\{([^}]+)\}", resume_tex) or \
        re.search(r"\\textbf\{([^}]+)\}", resume_tex)
    full_name = name_match.group(1).strip() if name_match else "Ibtasam Ahmad"
    parts = full_name.split()
    details["first_name"] = parts[0] if parts else "Ibtasam"
    details["last_name"] = " ".join(parts[1:]) if len(parts) > 1 else "Ahmad"

    email_match = re.search(r"mailto:([^}]+)", resume_tex)
    details["email"] = email_match.group(1) if email_match else "shibtasam@gmail.com"

    phone_match = re.search(r"(\+\d[\d\s]{6,})", resume_tex)
    details["phone"] = phone_match.group(1).strip() if phone_match else "+92 315 0180953"

    li_match = re.search(r"linkedin\.com/[^}\s]+", resume_tex)
    details["linkedin"] = li_match.group(0) if li_match else "linkedin.com/in/ibtasam-ahmad"

    gh_match = re.search(r"github\.com/[^}\s]+", resume_tex)
    details["github"] = gh_match.group(0) if gh_match else "github.com/Ibtasam-Ahmad"

    details["city"] = HOME_CITY
    details["country"] = HOME_COUNTRY
    details["province"] = "Punjab"
    details["zip_code"] = "54000"
    details["address"] = f"{HOME_CITY}, Punjab, {HOME_COUNTRY}"
    details["notice_period"] = "Immediate"
    details["visa_status"] = "Eligible for employer-sponsored work visa"
    return details


PERSONAL_DETAILS = extract_personal_details(BASE_RESUME_LATEX)


# ═════════════════════════════════════════════════════════════════════════════
#  STYLING
# ═════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 26px 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 6px 20px rgba(102,126,234,0.35);
    }
    .hero h1 { color: white; margin: 0; font-size: 30px; }
    .hero p  { color: #eef1ff; margin: 6px 0 0 0; font-size: 15px; }

    .output-card {
        background: #ffffff;
        border: 1px solid #eaeaf0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin: 8px 0 16px 0;
    }
    .changes-box {
        background: #f6f9ff;
        border-left: 4px solid #667eea;
        border-radius: 10px;
        padding: 14px 18px;
        margin: 6px 0 18px 0;
    }
    .badge {
        display: inline-block;
        padding: 3px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
    }
    .badge-blue  { background: #e7edff; color: #3b4cca; }
    .badge-green { background: #e3f6ec; color: #1a8f4c; }
    .badge-amber { background: #fdf0dd; color: #b5730f; }
    .stCode pre { font-size: 13px; }
    .section-header { color: #4a4a68; font-weight: 600; font-size: 18px; margin: 18px 0 8px; }
</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ═════════════════════════════════════════════════════════════════════════════

def init_session_state() -> None:
    defaults = {
        "stage": "input",          # input -> review -> done
        "pending_action": None,    # regenerate | reset (processed before widgets)
        "draft": {},               # AI output before approval
        "final": {},               # compiled PDFs + approved text
        "changes": {},             # {"resume":[...], "cover":[...], "extra":[...]}
        "job_title": "",
        # remembered generation inputs (so "Regenerate" can reuse them)
        "gen_job_text": "",
        "gen_app_mode": "email",
        "gen_work_mode": "Onsite",
        "gen_location": "",
        "gen_model": "llama-3.3-70b-versatile",
        "gen_temp": 0.2,
        "qa_count": 0,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


init_session_state()


# ═════════════════════════════════════════════════════════════════════════════
#  GROQ CLIENT WITH SMART MULTI-KEY FALLBACK
# ═════════════════════════════════════════════════════════════════════════════

class GroqClientManager:
    """Loads multiple Groq keys and rotates ONLY on rate-limit / auth / connection errors."""

    def __init__(self):
        self.keys: List[str] = []
        self.current_index: int = 0
        self._load_keys()

    def _load_keys(self) -> None:
        found: List[str] = []
        for i in range(1, 20):
            for prefix in ("GROQ_API_KEY_", "groq_api_key_"):
                name = f"{prefix}{i}"
                if name in st.secrets:
                    found.append(st.secrets[name])
        for name in ("GROQ_API_KEY", "groq_api_key"):
            if name in st.secrets:
                found.append(st.secrets[name])
        if "GROQ_API_KEYS" in st.secrets:
            val = st.secrets["GROQ_API_KEYS"]
            if isinstance(val, list):
                found.extend(val)
            elif isinstance(val, str):
                found.extend([k.strip() for k in val.split(",") if k.strip()])

        seen = set()
        for k in found:
            if k and k not in seen:
                seen.add(k)
                self.keys.append(k)

        if not self.keys:
            st.error("No Groq API keys found in `.streamlit/secrets.toml`. Add GROQ_API_KEY_1 = \"gsk_...\".")
            st.stop()

    def _client(self) -> Groq:
        return Groq(api_key=self.keys[self.current_index])

    def _rotate(self) -> None:
        self.current_index = (self.current_index + 1) % len(self.keys)

    @staticmethod
    def _should_rotate(err: Exception) -> bool:
        """Rotate the key only for transient/quota/auth problems, not for bad requests."""
        status = getattr(err, "status_code", None) or getattr(err, "status", None)
        if status in (401, 403, 429, 500, 502, 503):
            return True
        name = type(err).__name__.lower()
        if any(t in name for t in ("ratelimit", "authentication", "permission", "connection", "apitimeout", "internalserver")):
            return True
        text = str(err).lower()
        return any(t in text for t in ("rate limit", "429", "quota", "invalid api key", "unauthorized"))

    def call(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.3,
        # max_tokens: int = 8000,
        response_format: Optional[Dict] = None,
    ) -> str:
        attempts = 0
        last_error = None
        while attempts < len(self.keys):
            try:
                kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    # "max_tokens": max_tokens,
                }
                if response_format:
                    kwargs["response_format"] = response_format
                resp = self._client().chat.completions.create(**kwargs)
                return resp.choices[0].message.content
            except Exception as e:  # noqa: BLE001
                last_error = e
                if self._should_rotate(e) and len(self.keys) > 1:
                    attempts += 1
                    self._rotate()
                    st.sidebar.warning(f"⚠️ Key rotated ({attempts}/{len(self.keys)}): {str(e)[:70]}")
                    continue
                # Non-transient error (bad prompt, model gone, JSON, etc.) — don't burn keys.
                raise
        raise RuntimeError(f"All {len(self.keys)} Groq keys failed. Last error: {last_error}")


# ═════════════════════════════════════════════════════════════════════════════
#  LATEX HELPERS
# ═════════════════════════════════════════════════════════════════════════════

_UNICODE_FIXES = {
    "–": "--", "—": "---", "‘": "`", "’": "'",
    "“": "``", "”": "''", "…": r"\ldots{}", " ": "~",
    "•": r"\textbullet{}", "é": r"\'e", "−": "-",
}


def sanitize_latex_for_pdflatex(latex: str) -> str:
    """Replace common unicode chars pdflatex chokes on with LaTeX-safe equivalents."""
    for bad, good in _UNICODE_FIXES.items():
        latex = latex.replace(bad, good)
    return latex


def clean_latex_output(raw: str) -> str:
    """Strip markdown fences and keep only \\documentclass ... \\end{document}."""
    raw = re.sub(r"```(?:latex|tex)?", "", raw, flags=re.IGNORECASE)
    raw = raw.replace("```", "").strip()
    start = raw.find("\\documentclass")
    if start > 0:
        raw = raw[start:]
    end = raw.rfind("\\end{document}")
    if end != -1:
        raw = raw[: end + len("\\end{document}")]
    return raw.strip()


def _parse_bullets(text: str) -> List[str]:
    bullets = []
    for line in text.splitlines():
        line = line.strip().lstrip("-*•%").strip()
        line = re.sub(r"^\d+[.)]\s*", "", line)
        if line:
            bullets.append(line)
    return bullets[:8]


def split_latex_and_changes(raw: str) -> Tuple[str, List[str]]:
    """Split model output into (clean latex, list of change bullets)."""
    if CHANGE_MARKER in raw:
        latex_part, _, changes_part = raw.partition(CHANGE_MARKER)
    else:
        latex_part, changes_part = raw, ""
    return clean_latex_output(latex_part), _parse_bullets(changes_part)


def compile_latex_to_pdf(latex_content: str, output_filename: str = "output") -> Tuple[Optional[bytes], str]:
    """Compile LaTeX -> PDF. Returns (pdf_bytes|None, log_message)."""
    latex_content = sanitize_latex_for_pdflatex(latex_content)
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, f"{output_filename}.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_content)
        try:
            log = ""
            for _ in range(2):
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
                     "-output-directory", tmpdir, tex_path],
                    capture_output=True, text=True, timeout=90,
                )
                log = result.stdout
            pdf_path = os.path.join(tmpdir, f"{output_filename}.pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    return f.read(), "ok"
            # extract the first LaTeX error line for a useful message
            err_line = next((ln for ln in log.splitlines() if ln.startswith("!")), "")
            return None, f"pdflatex ran but produced no PDF. {err_line}".strip()
        except FileNotFoundError:
            return None, "pdflatex-not-found"
        except subprocess.TimeoutExpired:
            return None, "LaTeX compilation timed out."
        except Exception as e:  # noqa: BLE001
            return None, f"LaTeX error: {e}"


# ═════════════════════════════════════════════════════════════════════════════
#  LOCATION / WORK-MODE DIRECTIVE
# ═════════════════════════════════════════════════════════════════════════════

def build_location_directive(work_mode: str, job_location: str) -> str:
    loc = (job_location or "").strip()
    wm = work_mode.strip().lower()

    if wm == "remote":
        return (
            "WORK ARRANGEMENT: FULLY REMOTE.\n"
            "- REMOVE every relocation statement everywhere: the header tagline, the Professional "
            "Summary closing line, the 'Languages & Relocation' row, and every relocation sentence "
            "in the cover letter and email.\n"
            "- Do NOT sell relocation or visa sponsorship.\n"
            "- INSTEAD emphasize proven remote / distributed collaboration, strong async "
            "communication, self-management, and reliable working-hours overlap with the team.\n"
            "- Header tagline: replace ': Open to Relocation' with ': Open to Remote Roles' "
            "(or simply the role focus)."
        )

    if not loc:
        return (
            f"WORK ARRANGEMENT: {work_mode.upper()} (specific location not provided).\n"
            "- Keep ONE concise, professional availability line; do not over-emphasize relocation."
        )

    is_home = HOME_CITY.lower() in loc.lower()
    if is_home:
        return (
            f"WORK ARRANGEMENT: {work_mode.upper()} in {loc} — this is the candidate's HOME city.\n"
            "- REMOVE all relocation language everywhere (header tagline, summary closing line, "
            "'Languages & Relocation' row, cover letter, email).\n"
            f"- Present the candidate as a LOCAL professional already based in {HOME_CITY}, "
            "available to start on-site immediately with zero relocation needed.\n"
            "- Header tagline: replace ': Open to Relocation' with the tailored role focus (no relocation)."
        )

    return (
        f"WORK ARRANGEMENT: {work_mode.upper()} in {loc}.\n"
        f"- The candidate currently lives in {HOME_CITY}, {HOME_COUNTRY} and will RELOCATE to {loc}.\n"
        f"- Replace EVERY generic relocation phrase (e.g. 'Middle East and Schengen countries', "
        f"'Open to Relocation', 'to the Middle East, Schengen countries, or any global tech hub') "
        f"with a SPECIFIC, confident commitment to {loc}, e.g. 'Immediately available to relocate to {loc}'.\n"
        f"- Update the header tagline and the 'Languages & Relocation' -> Relocation row to name {loc}.\n"
        f"- In the cover letter, name {loc} explicitly in the opening and the relocation paragraph.\n"
        "- Keep the visa-sponsorship eligibility line."
    )


# ═════════════════════════════════════════════════════════════════════════════
#  PROMPTS
# ═════════════════════════════════════════════════════════════════════════════

def resume_prompt(job_text, job_title, work_mode, job_location, directive) -> str:
    return f"""You are an elite resume writer and ATS-optimization specialist for AI/ML engineering roles.

GOAL: Produce a HIGHLY TAILORED, ATS-optimized LaTeX resume for THIS job, staying 100% truthful.

TRUTH RULES (non-negotiable):
- Use ONLY employers, dates, projects, metrics, degrees, and skills present in the base resume.
- NEVER invent employers, numbers, titles, or projects. You may rephrase, reorder, re-emphasize.

TAILORING INSTRUCTIONS:
1. Keep the EXACT LaTeX preamble, packages, and document structure so it compiles unchanged.
2. Rewrite the header tagline (line under the name) to reflect this job's focus (see directive for relocation part).
3. Rewrite the Professional Summary to hit the job's top 3-4 requirements using the JD's own terminology.
4. Reorder the Core Technologies rows and the items inside each row so JD-relevant skills come FIRST.
5. Reorder Projects so the most JD-relevant come first; rewrite their one-line descriptions to mirror JD keywords and outcomes.
6. Rewrite experience bullets with strong action verbs + quantified results, emphasizing JD-matching work.
7. Keep Education, Publications, and Certifications intact; de-emphasize clearly irrelevant content.
8. Inject the JD's important keywords naturally for ATS. Keep all real hyperlinks/contact info.

LOCATION & WORK-ARRANGEMENT DIRECTIVE (apply to header tagline, summary, and 'Languages & Relocation'):
{directive}

DETECTED JOB TITLE: {job_title}
WORK MODE: {work_mode}
JOB LOCATION: {job_location or "not specified"}

BASE RESUME (LaTeX):
```latex
{BASE_RESUME_LATEX}
```

JOB DESCRIPTION:
```
{job_text}
```

OUTPUT FORMAT — follow EXACTLY:
- First output ONLY the complete tailored LaTeX document (\\documentclass ... \\end{{document}}). No fences, no commentary.
- Then a new line with exactly: {CHANGE_MARKER}
- Then 4-7 bullet points (each starting with "- ") naming the key changes and why they fit this job.
"""


def cover_letter_prompt(job_text, job_title, company, work_mode, job_location, directive) -> str:
    return f"""You are an elite cover-letter writer for senior AI engineering roles.

GOAL: A compelling, tailored LaTeX cover letter for THIS job, 100% truthful to the base letter/resume facts.

TRUTH RULES: Use only real experience/projects from the base letter. Never invent facts or numbers.

TAILORING INSTRUCTIONS:
1. Keep the EXACT LaTeX structure so it compiles unchanged.
2. Subject line: use the exact job title "{job_title}"{f' at {company}' if company else ''}.
3. Opening: an attention-grabbing hook specific to this role/company.
4. Body: address the JD's top 3 requirements with concrete proof (pick the 2-3 MOST relevant projects and describe them with JD keywords).
5. If a company name is present in the JD, address it specifically; otherwise keep "your organization".
6. Keep all hyperlinks/contact info. Output valid, compilable LaTeX.

LOCATION & WORK-ARRANGEMENT DIRECTIVE (apply to the opening + relocation paragraph):
{directive}

DETECTED JOB TITLE: {job_title}
COMPANY (if detected): {company or "not detected"}
WORK MODE: {work_mode}   JOB LOCATION: {job_location or "not specified"}

BASE COVER LETTER (LaTeX):
```latex
{BASE_COVER_LETTER_LATEX}
```

JOB DESCRIPTION:
```
{job_text}
```

OUTPUT FORMAT — follow EXACTLY:
- First output ONLY the complete tailored LaTeX document (\\documentclass ... \\end{{document}}). No fences, no commentary.
- Then a new line with exactly: {CHANGE_MARKER}
- Then 3-6 bullet points (each starting with "- ") naming the key changes and why they fit this job.
"""


def email_prompt(job_text, job_title, company, directive, d) -> str:
    return f"""You are an elite job-application email strategist writing as the applicant.

APPLICANT (use EXACTLY):
- Name: {d['first_name']} {d['last_name']}  | Role: AI/ML Engineer (4+ yrs)
- Email: {d['email']}  | Phone: {d['phone']}  | Base: {d['city']}, {d['country']}
- LinkedIn: {d['linkedin']}  | GitHub: {d['github']}
- Focus: LLM systems, RAG, multi-agent orchestration, computer vision, LangChain/LangGraph

LOCATION & WORK-ARRANGEMENT DIRECTIVE (shape any availability/relocation wording accordingly):
{directive}

TASK: Write a high-conversion application email for the "{job_title}" role{f' at {company}' if company else ''}.
RULES:
1. Subject: specific, benefit-driven, includes the role + a standout proof point + the name.
2. Body: 3-4 tight paragraphs, under ~180 words, tailored to THIS JD's top needs.
3. MUST include the sentence: "Please find attached my tailored resume and cover letter as PDFs."
4. Lead with the single most relevant achievement/metric for THIS job (truthful, from the profile).
5. Close with a clear CTA (e.g. a short call this week). Do not invent facts.

JOB DESCRIPTION:
```
{job_text}
```

OUTPUT (JSON only):
{{
  "email_subject": "...",
  "email_body": "...",
  "changes": ["short bullet on what you tailored", "..."]
}}
"""


def portal_qa_prompt(job_text, job_title, directive, d) -> str:
    return f"""You are an elite job-application strategist filling a job-portal form as {d['first_name']} {d['last_name']}.

TASK: Read the portal page text, detect ALL fields/questions, and produce optimized answers.

EXTRACTED PERSONAL DETAILS (use EXACTLY for personal fields):
- Full Name: {d['first_name']} {d['last_name']}   | Email: {d['email']}   | Phone: {d['phone']}
- City: {d['city']}   | Country: {d['country']}   | Province/State: {d['province']}   | Zip: {d['zip_code']}
- Address: {d['address']}   | Notice Period: {d['notice_period']}   | Visa: {d['visa_status']}
- LinkedIn: {d['linkedin']}   | GitHub / Portfolio: {d['github']}

LOCATION & WORK-ARRANGEMENT DIRECTIVE (use for relocation / current-location / willing-to-relocate fields):
{directive}

RULES:
1. Personal-info fields: use ONLY the exact details above.
2. "Key skills": order to match the JD, leading with skills the JD names.
3. Salary fields: "Negotiable / open to discussion" — never invent a number.
4. Open-ended questions: 2-4 sentence answers referencing REAL projects/metrics from the profile, with JD keywords.
5. "Why this role/company?": connect JD requirements to real experience.
6. Availability: "Immediate". Portfolio: provide GitHub + LinkedIn.
7. Never fabricate projects, numbers, or experience. Detected job title: "{job_title}".
8. If no explicit questions exist, generate the most common application questions for this JD and answer them.

JOB PORTAL PAGE TEXT:
```
{job_text}
```

OUTPUT (JSON only):
{{
  "questions": [{{"question": "exact question", "answer": "optimized answer"}}],
  "changes": ["short bullet on how answers were tailored", "..."]
}}
"""


# ═════════════════════════════════════════════════════════════════════════════
#  JD PARSING HELPERS
# ═════════════════════════════════════════════════════════════════════════════

_TITLE_KEYWORDS = ("engineer", "developer", "scientist", "manager", "lead",
                   "architect", "analyst", "consultant", "specialist",
                   "director", "researcher", "designer")


def extract_job_title(job_text: str) -> str:
    for line in job_text.strip().split("\n")[:15]:
        line = line.strip()
        if line and len(line) < 100 and any(k in line.lower() for k in _TITLE_KEYWORDS):
            return line
    first = job_text.strip().split("\n")[0].strip() if job_text.strip() else ""
    return first or "the Position"


def extract_company(job_text: str) -> str:
    m = re.search(r"(?:at|@|company:|employer:)\s+([A-Z][A-Za-z0-9&.\- ]{2,40})", job_text)
    if m:
        return m.group(1).strip().rstrip(".,")
    return ""


# ═════════════════════════════════════════════════════════════════════════════
#  GENERATION  (produces DRAFT — no PDF yet)
# ═════════════════════════════════════════════════════════════════════════════

def generate_all(job_text, app_mode, work_mode, job_location, model, temperature) -> bool:
    """Run the AI tailoring. Stores draft + change summary and moves to the review stage."""
    # remember inputs so "Regenerate" can reuse them
    st.session_state.gen_job_text = job_text
    st.session_state.gen_app_mode = app_mode
    st.session_state.gen_work_mode = work_mode
    st.session_state.gen_location = job_location
    st.session_state.gen_model = model
    st.session_state.gen_temp = temperature

    try:
        groq = GroqClientManager()
    except Exception as e:  # noqa: BLE001
        st.error(f"Failed to initialize Groq client: {e}")
        return False

    job_title = extract_job_title(job_text)
    company = extract_company(job_text)
    directive = build_location_directive(work_mode, job_location)
    st.session_state.job_title = job_title

    draft: Dict = {}
    changes: Dict[str, List[str]] = {"resume": [], "cover": [], "extra": []}

    # 1) Resume
    try:
        raw = groq.call(
            [{"role": "user", "content": resume_prompt(job_text, job_title, work_mode, job_location, directive)}],
            model=model, temperature=temperature, 
            # max_tokens=8000,
        )
        latex, ch = split_latex_and_changes(raw)
        draft["resume_latex"] = latex
        changes["resume"] = ch
    except Exception as e:  # noqa: BLE001
        st.error(f"❌ Resume tailoring failed: {e}")
        return False

    # 2) Cover letter
    try:
        raw = groq.call(
            [{"role": "user", "content": cover_letter_prompt(job_text, job_title, company, work_mode, job_location, directive)}],
            model=model, temperature=temperature, 
            # max_tokens=6000,
        )
        latex, ch = split_latex_and_changes(raw)
        draft["cover_latex"] = latex
        changes["cover"] = ch
    except Exception as e:  # noqa: BLE001
        st.error(f"❌ Cover letter generation failed: {e}")
        return False

    # 3) Mode-specific
    if app_mode == "email":
        try:
            raw = groq.call(
                [{"role": "user", "content": email_prompt(job_text, job_title, company, directive, PERSONAL_DETAILS)}],
                model=model, temperature=temperature, 
                # max_tokens=1500,
                response_format={"type": "json_object"},
            )
            data = json.loads(raw)
            draft["email_subject"] = data.get("email_subject", "")
            draft["email_body"] = data.get("email_body", "")
            changes["extra"] = data.get("changes", []) or []
        except Exception as e:  # noqa: BLE001
            st.warning(f"⚠️ Email generation failed ({e}); using a safe fallback you can edit.")
            draft["email_subject"] = f"Application for {job_title} — {PERSONAL_DETAILS['first_name']} {PERSONAL_DETAILS['last_name']}"
            draft["email_body"] = "Dear Hiring Manager,\n\nPlease find attached my tailored resume and cover letter as PDFs.\n\nBest regards,\nIbtasam Ahmad"
    else:
        try:
            raw = groq.call(
                [{"role": "user", "content": portal_qa_prompt(job_text, job_title, directive, PERSONAL_DETAILS)}],
                model=model, temperature=min(temperature, 0.2), 
                # max_tokens=6000,
                response_format={"type": "json_object"},
            )
            data = json.loads(raw)
            draft["qa"] = data.get("questions", []) or []
            changes["extra"] = data.get("changes", []) or []
        except Exception as e:  # noqa: BLE001
            st.warning(f"⚠️ Q&A generation failed ({e}). You can add answers manually.")
            draft["qa"] = []

    # seed the editable widgets
    st.session_state["edit_resume_tex"] = draft["resume_latex"]
    st.session_state["edit_cover_tex"] = draft["cover_latex"]
    if app_mode == "email":
        st.session_state["edit_email_subject"] = draft.get("email_subject", "")
        st.session_state["edit_email_body"] = draft.get("email_body", "")
    else:
        qa = draft.get("qa", [])
        st.session_state.qa_count = len(qa)
        for i, item in enumerate(qa):
            st.session_state[f"edit_q_{i}"] = item.get("question", "")
            st.session_state[f"edit_a_{i}"] = item.get("answer", "")

    draft["app_mode"] = app_mode
    st.session_state.draft = draft
    st.session_state.changes = changes
    st.session_state.final = {}
    st.session_state.stage = "review"
    return True


# ═════════════════════════════════════════════════════════════════════════════
#  UI PIECES
# ═════════════════════════════════════════════════════════════════════════════

def render_sidebar() -> Tuple[str, float]:
    with st.sidebar:
        st.title("⚙️ Settings")
        st.markdown("---")
        model = st.selectbox(
            "Groq Model",
            [
                "llama-3.3-70b-versatile",
                "llama-3.1-8b-instant",
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b",
                "gemma2-9b-it",
            ],
            index=0,
            help="70B is best for tailoring quality. 8B/gemma are faster/cheaper.",
        )
        temperature = st.slider(
            "Creativity (temperature)", 0.0, 1.0, 0.2, 0.1,
            help="Lower = more factual & conservative. Higher = more creative wording.",
        )
        st.markdown("---")
        st.markdown("### 👤 Profile (fixed)")
        st.markdown(f"**{PERSONAL_DETAILS['first_name']} {PERSONAL_DETAILS['last_name']}**")
        st.caption(f"📧 {PERSONAL_DETAILS['email']}")
        st.caption(f"📱 {PERSONAL_DETAILS['phone']}")
        st.caption(f"📍 {PERSONAL_DETAILS['city']}, {PERSONAL_DETAILS['country']}")
        st.markdown("---")
        st.markdown("### 🧭 How it works")
        st.markdown(
            "1. Pick mode, work type & location\n"
            "2. Paste the job description\n"
            "3. **Generate** → review & edit\n"
            "4. **Approve** → download PDFs"
        )
    return model, temperature


def render_input(model: str, temperature: float) -> None:
    st.markdown("### 1 · Application setup")
    c1, c2, c3 = st.columns([1.1, 1, 1.2])
    with c1:
        app_mode_label = st.radio("Application mode", ["📧 Email", "🌐 Job Portal"],
                                   index=0 if st.session_state.gen_app_mode == "email" else 1)
        app_mode = "email" if "Email" in app_mode_label else "portal"
    with c2:
        work_mode = st.radio("Work mode", ["Onsite", "Hybrid", "Remote"],
                             index=["Onsite", "Hybrid", "Remote"].index(st.session_state.gen_work_mode)
                             if st.session_state.gen_work_mode in ["Onsite", "Hybrid", "Remote"] else 0)
    with c3:
        job_location = st.text_input(
            "Job location (city, country)",
            value=st.session_state.gen_location,
            placeholder="e.g. Jeddah, KSA   ·   Lahore, Pakistan   ·   leave blank if unknown",
            disabled=(work_mode == "Remote"),
            help="Drives relocation wording. Remote ignores this and drops relocation language.",
        )

    # live hint about what will happen with relocation wording
    hint = _relocation_hint(work_mode, job_location)
    st.markdown(f"<div class='changes-box'>🧭 {hint}</div>", unsafe_allow_html=True)

    st.markdown("### 2 · Paste the job")
    job_text = st.text_area(
        "Job description / portal page text",
        value=st.session_state.gen_job_text,
        height=280,
        placeholder="Paste the full job description here.\nFor Job Portal mode, paste the ENTIRE page including all questions and fields.",
    )

    gen_col, _ = st.columns([0.28, 0.72])
    with gen_col:
        clicked = st.button("✨ Generate & Review", type="primary", use_container_width=True)

    if clicked:
        if not job_text.strip():
            st.error("Please paste the job text first.")
            return
        with st.spinner("🚀 Tailoring resume, cover letter & application… (~20-60s)"):
            ok = generate_all(job_text, app_mode, work_mode, job_location, model, temperature)
        if ok:
            st.rerun()


def _relocation_hint(work_mode: str, job_location: str) -> str:
    loc = (job_location or "").strip()
    if work_mode == "Remote":
        return "**Remote** → relocation lines removed; remote-collaboration strengths emphasized."
    if not loc:
        return "No location set → a neutral availability line will be kept."
    if HOME_CITY.lower() in loc.lower():
        return f"Location is **{loc}** (home city) → presented as a **local** candidate, no relocation."
    return f"Location is **{loc}** → documents will say **“immediately available to relocate to {loc}.”**"


def render_changes() -> None:
    ch = st.session_state.changes
    all_bullets = []
    for label, key in [("Resume", "resume"), ("Cover letter", "cover"),
                       ("Email/Q&A", "extra")]:
        for b in ch.get(key, []):
            all_bullets.append(f"**{label}:** {b}")
    if not all_bullets:
        return
    st.markdown("<div class='changes-box'>", unsafe_allow_html=True)
    st.markdown("#### 📝 What the AI changed for this job")
    for b in all_bullets:
        st.markdown(f"- {b}")
    st.markdown("</div>", unsafe_allow_html=True)


def render_review() -> None:
    st.markdown(
        f"<span class='badge badge-blue'>Job: {st.session_state.job_title}</span>"
        f"<span class='badge badge-amber'>{st.session_state.gen_work_mode}"
        f"{(' · ' + st.session_state.gen_location) if st.session_state.gen_location and st.session_state.gen_work_mode!='Remote' else ''}</span>"
        f"<span class='badge badge-green'>Review before building PDF</span>",
        unsafe_allow_html=True,
    )
    render_changes()
    st.info("Edit anything below. The PDFs are built from **exactly what you see here** when you approve.")

    app_mode = st.session_state.draft.get("app_mode", "email")
    tab_labels = ["📄 Resume (LaTeX)", "✉️ Cover Letter (LaTeX)",
                  "📧 Email" if app_mode == "email" else "🌐 Portal Q&A"]
    t_resume, t_cover, t_extra = st.tabs(tab_labels)

    with t_resume:
        st.text_area("Tailored resume LaTeX", key="edit_resume_tex", height=460)
    with t_cover:
        st.text_area("Tailored cover letter LaTeX", key="edit_cover_tex", height=460)
    with t_extra:
        if app_mode == "email":
            st.text_input("Email subject", key="edit_email_subject")
            st.text_area("Email body", key="edit_email_body", height=300)
        else:
            if st.session_state.qa_count == 0:
                st.warning("No questions detected. Paste more complete portal text and regenerate.")
            for i in range(st.session_state.qa_count):
                st.text_input(f"Q{i+1}", key=f"edit_q_{i}")
                st.text_area(f"Answer {i+1}", key=f"edit_a_{i}", height=110)
                st.markdown("---")

    st.markdown("")
    b1, b2, b3 = st.columns([0.3, 0.25, 0.25])
    with b1:
        approve = st.button("✅ Approve & Build PDFs", type="primary", use_container_width=True)
    with b2:
        if st.button("🔄 Regenerate", use_container_width=True):
            st.session_state.pending_action = "regenerate"
            st.rerun()
    with b3:
        if st.button("🆕 Start over", use_container_width=True):
            st.session_state.pending_action = "reset"
            st.rerun()

    if approve:
        _approve_and_build(app_mode)
        st.rerun()


def _approve_and_build(app_mode: str) -> None:
    with st.spinner("🛠️ Compiling PDFs from your edited version…"):
        resume_tex = st.session_state.get("edit_resume_tex", "")
        cover_tex = st.session_state.get("edit_cover_tex", "")
        resume_pdf, r_log = compile_latex_to_pdf(resume_tex, "Ibtasam_Ahmad_Resume")
        cover_pdf, c_log = compile_latex_to_pdf(cover_tex, "Ibtasam_Ahmad_Cover_Letter")

    final = {
        "app_mode": app_mode,
        "resume_tex": resume_tex,
        "cover_tex": cover_tex,
        "resume_pdf": resume_pdf,
        "cover_pdf": cover_pdf,
        "resume_log": r_log,
        "cover_log": c_log,
    }
    if app_mode == "email":
        final["email_subject"] = st.session_state.get("edit_email_subject", "")
        final["email_body"] = st.session_state.get("edit_email_body", "")
    else:
        qa = []
        for i in range(st.session_state.qa_count):
            qa.append({
                "question": st.session_state.get(f"edit_q_{i}", ""),
                "answer": st.session_state.get(f"edit_a_{i}", ""),
            })
        final["qa"] = qa

    st.session_state.final = final
    st.session_state.stage = "done"


def _pdflatex_help() -> None:
    st.warning(
        "⚠️ **pdflatex not found** — install a LaTeX distribution to build PDFs. "
        "You can still download the `.tex` source below and compile it (e.g. on Overleaf).\n\n"
        "- **Ubuntu/Debian:** `sudo apt-get install texlive-latex-base texlive-latex-extra texlive-fonts-recommended`\n"
        "- **macOS:** `brew install --cask mactex`\n"
        "- **Windows:** install MiKTeX (miktex.org)"
    )


def render_done() -> None:
    f = st.session_state.final
    job = st.session_state.job_title
    st.success(f"✅ Application materials ready for **{job}**")

    render_changes()

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='output-card'>", unsafe_allow_html=True)
        st.markdown("### 📄 Tailored Resume")
        _pdf_or_source("resume", f, job)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='output-card'>", unsafe_allow_html=True)
        st.markdown("### ✉️ Cover Letter")
        _pdf_or_source("cover", f, job)
        st.markdown("</div>", unsafe_allow_html=True)

    if f.get("app_mode") == "email":
        st.markdown("### 📧 Application Email")
        st.markdown("<div class='output-card'>", unsafe_allow_html=True)
        st.markdown("**Subject**")
        st.code(f.get("email_subject", ""), language="text")
        st.markdown("**Body**")
        st.code(f.get("email_body", ""), language="text")
        full = f"Subject: {f.get('email_subject','')}\n\n{f.get('email_body','')}"
        st.download_button("⬇️ Download full email (.txt)", full,
                           file_name="application_email.txt", mime="text/plain")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("### 🌐 Portal Questions & Answers")
        qa = f.get("qa", [])
        if not qa:
            st.warning("No Q&A captured.")
        for i, item in enumerate(qa):
            st.markdown("<div class='output-card'>", unsafe_allow_html=True)
            st.markdown(f"**Q{i+1}: {item.get('question','')}**")
            st.code(item.get("answer", ""), language="text")
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    b1, b2 = st.columns([0.25, 0.25])
    with b1:
        if st.button("✏️ Back to edit", use_container_width=True):
            st.session_state.stage = "review"
            st.rerun()
    with b2:
        if st.button("🆕 Start over", use_container_width=True):
            st.session_state.pending_action = "reset"
            st.rerun()


def _pdf_or_source(kind: str, f: Dict, job: str) -> None:
    pdf = f.get(f"{kind}_pdf")
    tex = f.get(f"{kind}_tex", "")
    log = f.get(f"{kind}_log", "")
    safe_job = re.sub(r"[^A-Za-z0-9]+", "_", job).strip("_")[:40] or "Application"
    nice = "Resume" if kind == "resume" else "Cover_Letter"
    if pdf:
        st.download_button(
            f"⬇️ Download {nice} PDF", data=pdf,
            file_name=f"Ibtasam_Ahmad_{nice}_{safe_job}.pdf",
            mime="application/pdf", use_container_width=True, key=f"dl_{kind}_pdf",
        )
    else:
        if log == "pdflatex-not-found":
            _pdflatex_help()
        else:
            st.warning(f"PDF build failed: {log}")
    st.download_button(
        f"⬇️ {nice} LaTeX (.tex)", data=tex,
        file_name=f"Ibtasam_Ahmad_{nice}_{safe_job}.tex",
        mime="text/x-tex", use_container_width=True, key=f"dl_{kind}_tex",
    )


# ═════════════════════════════════════════════════════════════════════════════
#  ACTION DISPATCH + MAIN
# ═════════════════════════════════════════════════════════════════════════════

def _reset_state() -> None:
    for k in list(st.session_state.keys()):
        if k.startswith(("edit_", "gen_")) or k in (
            "draft", "final", "changes", "job_title", "qa_count", "stage"):
            del st.session_state[k]
    init_session_state()


def process_pending_actions() -> None:
    """Runs BEFORE any review widgets are created, so we can safely reset their keys."""
    action = st.session_state.pop("pending_action", None)
    if action == "reset":
        _reset_state()
    elif action == "regenerate":
        with st.spinner("🔄 Regenerating…"):
            generate_all(
                st.session_state.gen_job_text,
                st.session_state.gen_app_mode,
                st.session_state.gen_work_mode,
                st.session_state.gen_location,
                st.session_state.gen_model,
                st.session_state.gen_temp,
            )


def main() -> None:
    process_pending_actions()
    model, temperature = render_sidebar()

    st.markdown(
        "<div class='hero'><h1>📄 AI Resume Tailor & Application Assistant</h1>"
        "<p>Job-specific resume + cover letter, location-aware relocation wording, "
        "and a review-before-download gate.</p></div>",
        unsafe_allow_html=True,
    )

    stage = st.session_state.stage
    if stage == "input":
        render_input(model, temperature)
    elif stage == "review":
        render_review()
    elif stage == "done":
        render_done()

    st.markdown("---")
    st.caption("Built by Ibtasam Ahmad · Powered by Groq")


if __name__ == "__main__":
    main()
