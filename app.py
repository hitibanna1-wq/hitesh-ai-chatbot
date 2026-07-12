import streamlit as st
from datetime import date
from ddgs import DDGS
from groq import Groq

st.set_page_config(
    page_title="Nivora AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] {font-family:'Inter',sans-serif;}
.stApp {background:radial-gradient(circle at 50% -20%,#192441 0%,#090d17 42%,#06080e 100%);}
[data-testid="stSidebar"] {background:rgba(8,12,22,.96);border-right:1px solid #20283a;}
[data-testid="stHeader"] {background:transparent;}
.block-container {max-width:960px;padding-top:2rem;padding-bottom:7rem;}
.brand {font-size:1.35rem;font-weight:700;letter-spacing:-.03em;margin-bottom:.2rem;}
.brand-dot {color:#7c8cff}.side-note {color:#818ba3;font-size:.78rem;margin-bottom:1.5rem;}
.hero {text-align:center;padding:3rem 1rem 2rem;}
.hero-badge {display:inline-block;color:#aab4ff;background:#151b33;border:1px solid #29325b;
padding:.35rem .75rem;border-radius:999px;font-size:.76rem;font-weight:600;letter-spacing:.05em;}
.hero h1 {font-size:clamp(2.2rem,6vw,4rem);line-height:1.05;letter-spacing:-.055em;margin:1rem 0 .7rem;
background:linear-gradient(100deg,#fff 20%,#a9b4ff 60%,#8ce8dc);-webkit-background-clip:text;color:transparent;}
.hero p {color:#9aa5ba;font-size:1.05rem;margin:auto;max-width:620px;}
.suggestion {padding:1rem 1.1rem;border:1px solid #222c40;border-radius:14px;background:#0e1422;
color:#c9d1df;min-height:88px;font-size:.9rem;}
[data-testid="stChatMessage"] {background:rgba(14,20,34,.68);border:1px solid #222c40;border-radius:18px;padding:1rem;}
[data-testid="stChatInput"] {border:1px solid #34405c;border-radius:18px;background:#101625;}
.stButton>button {border-radius:12px;border:1px solid #2b3650;background:#121a2b;color:#dce3f2;}
.stButton>button:hover {border-color:#7c8cff;color:white;}
hr {border-color:#20283a}.status {color:#78dcca;font-size:.78rem;}
</style>
""", unsafe_allow_html=True)

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are Nivora, a polished professional AI productivity assistant.
Answer in the same language as the user; understand Hindi, Hinglish, and English naturally.
Lead with the direct answer. Be accurate, practical, calm, and concise unless detail is requested.
Use short headings and bullets only when they improve clarity. Never use filler or exaggerated claims.
For instructions, give ordered, actionable steps. For business writing, produce ready-to-use copy.
When uncertain, say what is uncertain. Never invent facts, links, citations, or live information.
When web results are provided, rely on them, cite them as [1], [2], and separate facts from inference.
For risky medical, legal, or financial topics, state appropriate limitations and recommend a professional.
"""

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown('<div class="brand"><span class="brand-dot">✦</span> Nivora AI</div><div class="side-note">Your intelligent workspace</div>', unsafe_allow_html=True)
    if st.button("＋  New conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    web_search = st.toggle("Web intelligence", help="Search the live web before answering")
    response_style = st.selectbox("Response style", ["Balanced", "Concise", "Detailed"])
    st.divider()
    st.markdown('<div class="status">● Online & ready</div>', unsafe_allow_html=True)
    st.caption("AI can make mistakes. Verify important information.")

if not st.session_state.messages:
    st.markdown("""
    <div class="hero">
      <span class="hero-badge">YOUR AI WORKSPACE</span>
      <h1>What will you create today?</h1>
      <p>Research, write, analyse and turn ideas into polished work—through one intelligent conversation.</p>
    </div>
    """, unsafe_allow_html=True)
    cols = st.columns(3)
    cards = [
        ("Research", "Compare the best tools for a small online business"),
        ("Create", "Write a professional proposal for my client"),
        ("Plan", "Build a practical 30-day launch strategy"),
    ]
    for col, (title, text) in zip(cols, cards):
        col.markdown(f'<div class="suggestion"><b>{title}</b><br><span style="color:#8792a8">{text}</span></div>', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask Nivora anything...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    search_results = []
    model_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    model_messages.extend(st.session_state.messages)

    with st.chat_message("assistant"):
        try:
            if web_search:
                with st.spinner("Searching reliable sources..."):
                    search_results = list(DDGS().text(prompt, region="in-en", safesearch="moderate", max_results=6))
                web_context = "\n\n".join(
                    f"[{i}] {item.get('title','')}\n{item.get('body','')}\nURL: {item.get('href','')}"
                    for i, item in enumerate(search_results, 1)
                )
                model_messages[-1] = {
                    "role": "user",
                    "content": f"Date: {date.today().isoformat()}\n\nQuestion: {prompt}\n\nWeb results:\n{web_context}\n\nAnswer using these sources and cite factual claims [1], [2].",
                }

            style_instruction = {
                "Concise": "Keep the answer brief and focused.",
                "Detailed": "Give a thorough, structured answer with useful context.",
                "Balanced": "Use a balanced level of detail.",
            }[response_style]
            model_messages.append({"role": "system", "content": style_instruction})

            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=model_messages,
                    temperature=0.35,
                )
            answer = response.choices[0].message.content
            st.markdown(answer)

            if search_results:
                with st.expander("Sources"):
                    for i, item in enumerate(search_results, 1):
                        st.markdown(f"{i}. [{item.get('title','Source')}]({item.get('href','')})")
        except Exception as error:
            answer = "I couldn't complete that request right now. Please try again in a moment."
            st.error(answer)
            st.caption(f"Technical detail: {error}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
