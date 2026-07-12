import streamlit as st
from groq import Groq
from ddgs import DDGS
from datetime import date

client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.set_page_config(
    page_title="Hitesh AI",
    page_icon="🤖"
)

st.title("🤖 Hitesh Local AI")
st.caption("Local Gemma 3 chatbot with optional web search")

if "messages" not in st.session_state:
    st.session_state.messages = []

web_search = st.sidebar.toggle("🌐 Web Search")

if st.sidebar.button("New Chat"):
    st.session_state.messages = []
    st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Apna message likho...")

if prompt:
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    with st.chat_message("user"):
        st.markdown(prompt)

    model_messages = st.session_state.messages.copy()
    search_results = []

    with st.chat_message("assistant"):
        try:
            if web_search:
                with st.spinner("Internet par search ho raha hai..."):
                    search_results = DDGS(timeout=15).text(
                        prompt,
                        region="in-en",
                        safesearch="moderate",
                        max_results=5
                    )

                web_context = "\n\n".join(
                    f"[{number}] {result.get('title', '')}\n"
                    f"{result.get('body', '')}\n"
                    f"URL: {result.get('href', '')}"
                    for number, result in enumerate(search_results, start=1)
                )

                model_messages[-1] = {
                    "role": "user",
                    "content": f"""
Today's date: {date.today().isoformat()}

User question:
{prompt}

Web search results:
{web_context}

Answer in the user's language.
Use only reliable information from these results.
Cite sources using [1], [2], etc.
If results are insufficient, clearly say so.
"""
                }

            with st.spinner("Soch raha hoon..."):
                response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=model_messages
)

answer = response.choices[0].message.content

            answer = response.message.content
            st.markdown(answer)

            if search_results:
                with st.expander("Sources"):
                    for number, result in enumerate(search_results, start=1):
                        title = result.get("title", "Source")
                        url = result.get("href", "")
                        st.markdown(f"{number}. [{title}]({url})")

        except Exception as error:
            answer = f"Error: {error}"
            st.error(answer)

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })
