import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from vectorstore.store import ChromaVectorStore
from chatbot.retriever import RAGRetriever
from chatbot.chain import RAGChatbot
from chatbot.prompts import RAG_SYSTEM_PROMPT, format_context_for_prompt, construct_rag_user_prompt
import config


def test_retrieval():
    print("\n--- [TEST 1] Testing Semantic Similarity Retrieval against ChromaDB ---")
    store = ChromaVectorStore()
    retriever = RAGRetriever(vector_store=store, top_k=3)

    # 1. Cloud computing page 1 query
    q1 = "What are the primary cloud service models such as IaaS and PaaS?"
    res1 = retriever.retrieve(q1, top_k=2)
    assert len(res1) > 0, "No results returned for cloud service models!"
    top_hit_1 = res1[0]
    assert top_hit_1["source"] == "cloud_computing_primer.pdf", f"Expected cloud_computing_primer.pdf, got {top_hit_1['source']}"
    assert top_hit_1["page"] == 1, f"Expected page 1, got {top_hit_1['page']}"
    assert "IaaS" in top_hit_1["content"]
    print(f"✓ Page 1 PDF retrieval verified: '{top_hit_1['source']}', Page {top_hit_1['page']} (Score: {top_hit_1['score']:.4f})")

    # 2. Cloud computing page 2 query (SLA & multi-region)
    q2 = "What uptime SLA guarantee is provided for multi-region cloud deployments?"
    res2 = retriever.retrieve(q2, top_k=2)
    assert len(res2) > 0
    top_hit_2 = res2[0]
    assert top_hit_2["source"] == "cloud_computing_primer.pdf"
    assert top_hit_2["page"] == 2, f"Expected page 2, got {top_hit_2['page']}"
    assert "99.999" in top_hit_2["content"]
    print(f"✓ Page 2 PDF retrieval verified: '{top_hit_2['source']}', Page {top_hit_2['page']} (Score: {top_hit_2['score']:.4f})")

    # 3. AI Ethics DOCX query
    q3 = "What are the guidelines and required actions for high risk autonomous medical diagnosis?"
    res3 = retriever.retrieve(q3, top_k=2)
    assert len(res3) > 0
    top_hit_3 = res3[0]
    assert top_hit_3["source"] == "ai_ethics_guidelines.docx"
    assert "Autonomous Medical Diagnosis" in top_hit_3["content"]
    print(f"✓ DOCX table/text retrieval verified: '{top_hit_3['source']}', Page {top_hit_3['page']} (Score: {top_hit_3['score']:.4f})")

    # 4. Quantum Computing TXT query
    q4 = "How do qubits and superposition operate differently from classical bits?"
    res4 = retriever.retrieve(q4, top_k=2)
    assert len(res4) > 0
    top_hit_4 = res4[0]
    assert top_hit_4["source"] == "quantum_computing.txt"
    assert "superposition" in top_hit_4["content"].lower()
    print(f"✓ TXT retrieval verified: '{top_hit_4['source']}' (Score: {top_hit_4['score']:.4f})")


def test_prompt_construction():
    print("\n--- [TEST 2] Testing Grounded Prompt Construction & Citation Formatting ---")
    store = ChromaVectorStore()
    retriever = RAGRetriever(vector_store=store, top_k=2)

    chunks = retriever.retrieve("What is Grover's algorithm?")
    raw_docs = [c["raw_doc"] for c in chunks]
    formatted_context = format_context_for_prompt(raw_docs)

    assert "--- DOCUMENT 1 ---" in formatted_context
    assert "Source: quantum_computing.txt" in formatted_context
    assert "Grover" in formatted_context

    user_prompt = construct_rag_user_prompt("What is Grover's algorithm?", formatted_context)
    assert "CONTEXT DOCUMENTS:" in user_prompt
    assert "USER QUESTION:" in user_prompt
    assert "[Document: <filename>, Page: <page>]" in user_prompt
    print("✓ Prompt construction verified: successfully embedded strict citations formatting and context boundaries.")


def test_chatbot_query_pipeline():
    print("\n--- [TEST 3] Testing End-to-End Chatbot Pipeline Response & Sources ---")
    chatbot = RAGChatbot()

    # Query loaded document
    response = chatbot.query("What is Shor's algorithm and who invests in quantum hardware?")
    assert "answer" in response
    assert "sources" in response
    assert len(response["sources"]) > 0
    first_source = response["sources"][0]
    assert "source" in first_source
    assert "page" in first_source
    assert "snippet" in first_source
    print(f"✓ Chatbot query returned {len(response['sources'])} source citations.")
    print(f"  Top source: {first_source['source']} (Page {first_source['page']})")
    print(f"  Response preview: {response['answer'][:120]}...")

    # Query with completely empty / reset database behavior
    empty_store = ChromaVectorStore(collection_name="temp_empty_test_collection")
    empty_chatbot = RAGChatbot(vector_store=empty_store)
    empty_res = empty_chatbot.query("Can you tell me about quantum computing?")
    assert "no documents are currently loaded" in empty_res["answer"]
    print("✓ Handled empty vector database appropriately.")


if __name__ == "__main__":
    print("========================================")
    print(" RUNNING INDEPENDENT CHATBOT TESTS")
    print("========================================")
    test_retrieval()
    test_prompt_construction()
    test_chatbot_query_pipeline()
    print("\n>>> ALL CHATBOT PIPELINE TESTS PASSED SUCCESSFULLY! <<<\n")
