import streamlit as st
import requests
import sys
import os

# Set page config
st.set_page_config(
    page_title="Mini Agentic RAG",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS injection
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

/* Global settings */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Gradient Title */
.title-gradient {
    background: linear-gradient(135deg, #00C6FF, #0072FF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    font-size: 2.8rem;
    margin-bottom: 5px;
}

.subtitle-desc {
    color: #94a3b8;
    font-size: 1.1rem;
    margin-bottom: 25px;
}

/* Trace Card Styles */
.trace-card {
    background: rgba(30, 41, 59, 0.4);
    border-radius: 12px;
    padding: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    margin-top: 10px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
}
.trace-title {
    font-weight: 700;
    color: #38bdf8;
    font-size: 15px;
    margin-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.trace-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    font-size: 13.5px;
}
.trace-label {
    color: #94a3b8;
    font-weight: 500;
}
.trace-value {
    color: #f8fafc;
    font-weight: 600;
}
.badge {
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
}
.badge-hit { background-color: #065f46; color: #34d399; }
.badge-miss { background-color: #991b1b; color: #fca5a5; }
.badge-na { background-color: #374151; color: #9ca3af; }
.badge-tool { background-color: #1e3a8a; color: #93c5fd; }
.badge-model { background-color: #581c87; color: #d8b4fe; }
.badge-fallback-yes { background-color: #7c2d12; color: #fdba74; }
.badge-fallback-no { background-color: #1f2937; color: #9ca3af; }

</style>
""", unsafe_allow_html=True)

# App layout
st.markdown("<h1 class='title-gradient'>🤖 Mini Agentic RAG</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle-desc'>Ask anything, scrape websites, or upload documents to query the agentic knowledge base.</p>", unsafe_allow_html=True)

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

API_BASE_URL = "http://127.0.0.1:8000"

# Sidebar for document upload / URL ingestion
with st.sidebar:
    st.markdown("### 📤 Ingest New Knowledge")
    ingest_option = st.radio("Choose Ingestion Source:", ("Upload PDF", "Scrape URL"))
    
    if ingest_option == "Upload PDF":
        uploaded_file = st.file_uploader("Upload a PDF File", type=["pdf"])
        if uploaded_file is not None:
            if st.button("Process & Ingest PDF", use_container_width=True):
                with st.spinner("Parsing and embedding PDF..."):
                    try:
                        # Call FastAPI POST /load
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                        res = requests.post(f"{API_BASE_URL}/load", files=files)
                        
                        if res.status_code == 200:
                            data = res.json()
                            st.success(f"Successfully ingested {data['chunks_ingested']} chunks from '{uploaded_file.name}'!")
                        else:
                            st.error(f"Error: {res.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Failed to communicate with backend: {e}")
                        
    else:
        url_input = st.text_input("Enter Web URL:", placeholder="https://example.com/about")
        if url_input:
            if st.button("Scrape & Ingest URL", use_container_width=True):
                with st.spinner("Scraping web content and building vectors..."):
                    try:
                        # Call FastAPI POST /load
                        data = {"url": url_input}
                        res = requests.post(f"{API_BASE_URL}/load", data=data)
                        
                        if res.status_code == 200:
                            res_data = res.json()
                            st.success(f"Successfully ingested {res_data['chunks_ingested']} chunks from URL!")
                        else:
                            st.error(f"Error: {res.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Failed to communicate with backend: {e}")

# Display Chat History
for chat in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(chat["query"])
    with st.chat_message("assistant"):
        st.write(chat["response"])
        
        # Format Trace HTML
        trace = chat["trace"]
        trace_html = f"""
        <div class="trace-card">
            <div class="trace-title">🔍 Execution Trace</div>
            <div class="trace-item">
                <span class="trace-label">Retrieval Status:</span>
                <span class="badge badge-{trace['retrieval'].lower()}">{trace['retrieval']}</span>
            </div>
            <div class="trace-item">
                <span class="trace-label">Tool/Route Used:</span>
                <span class="badge badge-tool">{trace['tool_used']}</span>
            </div>
            <div class="trace-item">
                <span class="trace-label">Model Used:</span>
                <span class="badge badge-model">{trace['model_used']}</span>
            </div>
            <div class="trace-item">
                <span class="trace-label">Fallback Triggered:</span>
                <span class="badge badge-fallback-{trace['fallback_triggered'].lower()}">{trace['fallback_triggered']}</span>
            </div>
            <div class="trace-item">
                <span class="trace-label">Response Time:</span>
                <span class="trace-value">{trace['response_time']}s</span>
            </div>
        </div>
        """
        st.markdown(trace_html, unsafe_allow_html=True)

# User query input
query = st.chat_input("Ask anything...")

if query:
    # Display user's question
    with st.chat_message("user"):
        st.write(query)
        
    # Process query
    with st.spinner("Thinking..."):
        try:
            # Call FastAPI POST /query
            res = requests.post(f"{API_BASE_URL}/query", json={"query": query})
            if res.status_code == 200:
                data = res.json()
                response = data["response"]
                trace = data["trace"]
            else:
                response = f"Backend error: {res.json().get('detail', 'Unknown error')}"
                trace = {
                    "retrieval": "N/A",
                    "tool_used": "None",
                    "model_used": "None",
                    "fallback_triggered": "No",
                    "response_time": 0.0
                }
        except Exception as e:
            response = f"Failed to communicate with backend: {e}"
            trace = {
                "retrieval": "N/A",
                "tool_used": "None",
                "model_used": "None",
                "fallback_triggered": "No",
                "response_time": 0.0
            }
        
    # Display response
    with st.chat_message("assistant"):
        st.write(response)
        
        # Display Trace Panel
        trace_html = f"""
        <div class="trace-card">
            <div class="trace-title">🔍 Execution Trace</div>
            <div class="trace-item">
                <span class="trace-label">Retrieval Status:</span>
                <span class="badge badge-{trace['retrieval'].lower()}">{trace['retrieval']}</span>
            </div>
            <div class="trace-item">
                <span class="trace-label">Tool/Route Used:</span>
                <span class="badge badge-tool">{trace['tool_used']}</span>
            </div>
            <div class="trace-item">
                <span class="trace-label">Model Used:</span>
                <span class="badge badge-model">{trace['model_used']}</span>
            </div>
            <div class="trace-item">
                <span class="trace-label">Fallback Triggered:</span>
                <span class="badge badge-fallback-{trace['fallback_triggered'].lower()}">{trace['fallback_triggered']}</span>
            </div>
            <div class="trace-item">
                <span class="trace-label">Response Time:</span>
                <span class="trace-value">{trace['response_time']}s</span>
            </div>
        </div>
        """
        st.markdown(trace_html, unsafe_allow_html=True)
        
    # Save to history
    st.session_state.chat_history.append({
        "query": query,
        "response": response,
        "trace": trace
    })