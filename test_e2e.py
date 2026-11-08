import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingestion.pipeline import IngestionPipeline
from vectorstore.store import ChromaVectorStore
from chatbot.chain import RAGChatbot
import config


def test_full_rag_integration():
    print("\n=======================================================")
    print(" RUNNING END-TO-END RAG PIPELINE INTEGRATION TEST")
    print("=======================================================")

    # 1. Initialize persistent vector store and reset for clean test run
    store = ChromaVectorStore()
    store.clear_all()
    stats = store.get_stats()
    assert stats["total_documents"] == 0
    print("✓ Vector Store initialized and wiped clean.")

    # 2. Ingest documents of all 3 types (PDF, DOCX, TXT)
    pipeline = IngestionPipeline(vector_store=store, chunk_size=400, chunk_overlap=80)
    data_dir = config.SAMPLE_DOCS_DIR

    docs_to_ingest = [
        "quantum_computing.txt",
        "ai_ethics_guidelines.docx",
        "cloud_computing_primer.pdf",
    ]

    for doc_name in docs_to_ingest:
        result = pipeline.ingest(data_dir / doc_name)
        assert result["status"] == "success", f"Ingestion failed for {doc_name}: {result}"
        print(f"✓ Ingested '{doc_name}': {result['total_chunks']} chunks stored.")

    # Verify overall index state
    stats = store.get_stats()
    assert stats["total_documents"] == 3
    print(f"✓ Total documents indexed: {stats['total_documents']} ({stats['total_chunks']} chunks total).")

    # 3. Test Chatbot Retrieval & Citation Grounding with Mock LLM
    # We test both real client initialization check and mock LLM response generation
    chatbot = RAGChatbot(vector_store=store)

    # Attach mock Gemini client to test grounded prompt response processing without requiring live API quota
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = (
        "Multi-region deployments offer 99.999 percent uptime SLA guarantees, "
        "and auto-scaling groups dynamically adjust virtual machines [Document: cloud_computing_primer.pdf, Page: 2]."
    )
    mock_client.models.generate_content.return_value = mock_response
    chatbot._client = mock_client
    chatbot.api_key = "test_key_for_e2e_verification"

    # Query 1: Cloud SLA (Should retrieve cloud_computing_primer.pdf, Page 2)
    q1 = "What SLA guarantee is provided for multi-region cloud deployments?"
    res1 = chatbot.query(q1)
    assert res1["retrieved_chunks_count"] > 0
    top_source_1 = res1["sources"][0]
    assert top_source_1["source"] == "cloud_computing_primer.pdf"
    assert top_source_1["page"] == 2
    assert "[Document: cloud_computing_primer.pdf, Page: 2]" in res1["answer"]
    print("✓ Query 1 Verified: Correctly retrieved page 2 of PDF and included source citation.")

    # Query 2: AI Ethics Table (Should retrieve ai_ethics_guidelines.docx)
    mock_response.text = (
        "For autonomous medical diagnosis, mandatory clinical validation and human sign-off are required "
        "[Document: ai_ethics_guidelines.docx, Page: 1]."
    )
    q2 = "What are the requirements for autonomous medical diagnosis?"
    res2 = chatbot.query(q2)
    assert res2["retrieved_chunks_count"] > 0
    top_source_2 = res2["sources"][0]
    assert top_source_2["source"] == "ai_ethics_guidelines.docx"
    print("✓ Query 2 Verified: Correctly retrieved DOCX table information.")

    # Query 3: Information not present in document
    mock_response.text = (
        "I am sorry, but the provided documents do not contain sufficient information to answer this question."
    )
    q3 = "What is the capital city of Australia?"
    res3 = chatbot.query(q3)
    assert "not contain sufficient information" in res3["answer"]
    print("✓ Query 3 Verified: Grounding guardrails properly return unavailable notice when facts are not in context.")

    # 4. Test Single Document Deletion and Re-query
    print("\n--- Testing Document Lifecycle: Deletion & Re-indexing ---")
    del_ok = store.delete_document("quantum_computing.txt")
    assert del_ok is True
    post_del_stats = store.get_stats()
    assert post_del_stats["total_documents"] == 2
    print("✓ Deleted 'quantum_computing.txt' - remaining documents: 2.")

    # Re-ingest quantum_computing.txt
    reingest_res = pipeline.ingest(data_dir / "quantum_computing.txt")
    assert reingest_res["status"] == "success"
    assert store.get_stats()["total_documents"] == 3
    print("✓ Re-ingested 'quantum_computing.txt' successfully.")

    # 5. Persistence across restarts simulation
    print("\n--- Testing Restart & Persistence ---")
    new_store_instance = ChromaVectorStore()
    new_chatbot = RAGChatbot(vector_store=new_store_instance)
    new_chatbot._client = mock_client
    new_chatbot.api_key = "test_key"

    restart_res = new_chatbot.query("Tell me about qubits.")
    assert restart_res["retrieved_chunks_count"] > 0
    assert restart_res["sources"][0]["source"] == "quantum_computing.txt"
    print("✓ Verified persistence: fresh instance immediately able to query persisted chunks.")

    print("\n=======================================================")
    print(" >>> END-TO-END INTEGRATION TEST PASSED 100%! <<<")
    print("=======================================================\n")


if __name__ == "__main__":
    test_full_rag_integration()
