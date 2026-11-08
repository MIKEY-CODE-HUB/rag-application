import os
import streamlit as st
from pathlib import Path
import config
from vectorstore.store import ChromaVectorStore
from ingestion.pipeline import IngestionPipeline
from chatbot.chain import RAGChatbot

# Page Configuration
st.set_page_config(
    page_title="Enterprise RAG System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #6c757d;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .source-card {
        border-left: 3px solid #4f46e5;
        background-color: #f8fafc;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
        border-radius: 4px;
        font-size: 0.9rem;
    }
    .source-header {
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.25rem;
    }
    .badge {
        display: inline-block;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 9999px;
        margin-right: 0.4rem;
    }
    .badge-pdf { background-color: #fee2e2; color: #991b1b; }
    .badge-docx { background-color: #dbeafe; color: #1e40af; }
    .badge-txt { background-color: #fef3c7; color: #92400e; }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "api_key" not in st.session_state:
    st.session_state.api_key = config.GEMINI_API_KEY or ""

if "vector_store" not in st.session_state:
    st.session_state.vector_store = ChromaVectorStore()

if "chatbot" not in st.session_state:
    st.session_state.chatbot = RAGChatbot(
        api_key=st.session_state.api_key,
        vector_store=st.session_state.vector_store,
        top_k=config.DEFAULT_TOP_K,
    )


# -------------------------------------------------------------
# SIDEBAR: Configuration & Document Ingestion
# -------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    # API Key Input
    api_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="Enter your Gemini API Key",
        help="Required for AI generation. Embeddings and semantic retrieval work locally.",
    )

    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.session_state.chatbot.set_api_key(api_key_input)
        st.rerun()

    if st.session_state.api_key:
        st.success("✓ Gemini API Key configured", icon="🔑")
    else:
        st.info("💡 Embeddings run locally via HuggingFace. Provide a Gemini API key for generated responses.", icon="ℹ️")

    st.markdown("---")

    # Chunking Hyperparameters Expander
    with st.expander("🛠️ Ingestion Parameters", expanded=False):
        chunk_size = st.slider("Chunk Size (characters)", 200, 2000, config.DEFAULT_CHUNK_SIZE, step=50)
        chunk_overlap = st.slider("Chunk Overlap (characters)", 0, 500, config.DEFAULT_CHUNK_OVERLAP, step=25)
        top_k = st.slider("Retrieved Chunks (Top-K)", 1, 10, config.DEFAULT_TOP_K, step=1)
        st.session_state.chatbot.retriever.top_k = top_k

    # Document Ingestion Section
    st.header("📄 Document Ingestion")
    uploaded_files = st.file_uploader(
        "Upload Documents (PDF, TXT, DOCX)",
        type=["pdf", "txt", "docx"],
        accept_multiple_files=True,
        help="Upload multiple documents for chunking, embedding, and indexing.",
    )

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        ingest_clicked = st.button("🚀 Ingest Files", use_container_width=True, disabled=not uploaded_files)
    with col_btn2:
        load_samples_clicked = st.button("📂 Load Samples", use_container_width=True, help="Load pre-built PDF, DOCX, and TXT samples")

    # Ingestion Processing
    if ingest_clicked and uploaded_files:
        pipeline = IngestionPipeline(
            vector_store=st.session_state.vector_store,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        progress_bar = st.progress(0)
        status_box = st.empty()

        for idx, uploaded_file in enumerate(uploaded_files):
            status_box.text(f"Processing '{uploaded_file.name}'...")
            result = pipeline.ingest(file_source=uploaded_file, file_name=uploaded_file.name)

            if result["status"] == "success":
                st.success(
                    f"✓ **{result['file_name']}**: {result['total_chunks']} chunks indexed ({result['total_pages']} pages).",
                    icon="✅"
                )
            elif result["status"] == "skipped":
                st.info(f"ℹ️ **{result['file_name']}**: Skipped duplicate (already indexed).", icon="⏭️")
            else:
                st.error(f"❌ **{result['file_name']}**: {result.get('message', 'Failed to ingest')}")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        status_box.text("Ingestion completed!")
        st.rerun()

    # Load Sample Documents Trigger
    if load_samples_clicked:
        sample_dir = config.SAMPLE_DOCS_DIR
        pipeline = IngestionPipeline(vector_store=st.session_state.vector_store)
        sample_files = list(sample_dir.glob("*.*"))

        if not sample_files:
            st.warning("No sample files found in sample directory.")
        else:
            for s_file in sample_files:
                if s_file.suffix.lower() in [".pdf", ".docx", ".txt"]:
                    res = pipeline.ingest(s_file)
                    if res["status"] == "success":
                        st.success(f"Loaded sample: {s_file.name}")
                    elif res["status"] == "skipped":
                        st.info(f"Sample '{s_file.name}' already indexed.")
            st.rerun()

    st.markdown("---")

    # Vector Store Management
    st.header("🗄️ Vector Database")
    stats = st.session_state.vector_store.get_stats()
    c1, c2 = st.columns(2)
    c1.metric("Documents", stats.get("total_documents", 0))
    c2.metric("Total Chunks", stats.get("total_chunks", 0))

    indexed_docs = st.session_state.vector_store.get_indexed_documents()
    if indexed_docs:
        with st.expander("📋 Indexed Document Library", expanded=False):
            for doc in indexed_docs:
                doc_name = doc["source"]
                file_ext = doc.get("file_type", "txt")
                col_d1, col_d2 = st.columns([4, 1])
                with col_d1:
                    st.markdown(f"**{doc_name}**  \n`{doc['chunk_count']} chunks` | `Pages: {', '.join(map(str, doc.get('pages', [1])))}`")
                with col_d2:
                    if st.button("🗑️", key=f"del_{doc_name}", help=f"Delete {doc_name}"):
                        st.session_state.vector_store.delete_document(doc_name)
                        st.rerun()
                st.divider()

    if st.button("⚠️ Clear Entire Database", use_container_width=True):
        st.session_state.vector_store.clear_all()
        st.session_state.chat_history = []
        st.success("Vector store cleared.")
        st.rerun()


# -------------------------------------------------------------
# MAIN CHAT PANEL
# -------------------------------------------------------------
st.markdown('<div class="main-title">Enterprise RAG Assistant</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Accurate, grounded answers strictly derived from your uploaded documents with verifiable source citations.</div>',
    unsafe_allow_html=True,
)

# Quick Action Bar
col_top1, col_top2 = st.columns([6, 1])
with col_top2:
    if st.button("🧹 Clear Chat", use_container_width=True, help="Clear message history"):
        st.session_state.chat_history = []
        st.rerun()

# Display Chat Messages from History
for message in st.session_state.chat_history:
    role = message["role"]
    content = message["content"]
    sources = message.get("sources", [])

    with st.chat_message(role):
        st.markdown(content)
        if sources:
            with st.expander(f"📚 Source Citations ({len(sources)} chunks retrieved)", expanded=False):
                for s in sources:
                    badge_class = f"badge-{s.get('source', '').split('.')[-1].lower()}"
                    st.markdown(
                        f"""<div class="source-card">
                            <div class="source-header">
                                <span class="badge {badge_class}">{s.get('source', 'Unknown')}</span>
                                <span>Page {s.get('page', 1)} | Chunk #{s.get('chunk_index', 0)} | Similarity Score: {s.get('score', 0.0)}</span>
                            </div>
                            <div style="color: #475569; font-style: italic;">"{s.get('snippet', '')}"</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )

# Chat Input & Response Handling
prompt = st.chat_input("Ask a question grounded in your uploaded documents...")

if prompt:
    # 1. Append and display user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Query RAG Chatbot
    with st.chat_message("assistant"):
        with st.spinner("Retrieving document chunks & generating grounded answer..."):
            response = st.session_state.chatbot.query(prompt)
            answer_text = response.get("answer", "No response generated.")
            sources = response.get("sources", [])

            st.markdown(answer_text)

            if sources:
                with st.expander(f"📚 Source Citations ({len(sources)} chunks retrieved)", expanded=False):
                    for s in sources:
                        badge_class = f"badge-{s.get('source', '').split('.')[-1].lower()}"
                        st.markdown(
                            f"""<div class="source-card">
                                <div class="source-header">
                                    <span class="badge {badge_class}">{s.get('source', 'Unknown')}</span>
                                    <span>Page {s.get('page', 1)} | Chunk #{s.get('chunk_index', 0)} | Similarity Score: {s.get('score', 0.0)}</span>
                                </div>
                                <div style="color: #475569; font-style: italic;">"{s.get('snippet', '')}"</div>
                            </div>""",
                            unsafe_allow_html=True,
                        )

            # Store in session state
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": answer_text,
                "sources": sources,
            })
