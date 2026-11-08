import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ingestion.document_loader import DocumentLoader
from ingestion.text_splitter import DocumentChunker
from ingestion.pipeline import IngestionPipeline
from vectorstore.store import ChromaVectorStore
import config

def test_document_loaders():
    print("\n--- [TEST 1] Testing Document Extractors (TXT, DOCX, PDF) ---")
    data_dir = config.SAMPLE_DOCS_DIR

    # 1. TXT
    txt_docs = DocumentLoader.load(data_dir / "quantum_computing.txt")
    assert len(txt_docs) == 1, f"Expected 1 doc, got {len(txt_docs)}"
    assert txt_docs[0].metadata["file_type"] == "txt"
    assert "qubits" in txt_docs[0].page_content.lower()
    print("✓ TXT Loader passed: extracted content and verified metadata.")

    # 2. DOCX
    docx_docs = DocumentLoader.load(data_dir / "ai_ethics_guidelines.docx")
    assert len(docx_docs) == 1, f"Expected 1 doc, got {len(docx_docs)}"
    assert docx_docs[0].metadata["file_type"] == "docx"
    assert "Transparency" in docx_docs[0].page_content
    assert "Autonomous Medical Diagnosis" in docx_docs[0].page_content  # Table row
    print("✓ DOCX Loader passed: extracted paragraphs and table rows.")

    # 3. PDF
    pdf_docs = DocumentLoader.load(data_dir / "cloud_computing_primer.pdf")
    assert len(pdf_docs) == 2, f"Expected 2 pages, got {len(pdf_docs)}"
    assert pdf_docs[0].metadata["page"] == 1
    assert pdf_docs[1].metadata["page"] == 2
    assert "IaaS" in pdf_docs[0].page_content
    assert "SLA" in pdf_docs[1].page_content
    print("✓ PDF Loader passed: extracted 2 distinct pages with exact 1-based page numbers.")


def test_chunking():
    print("\n--- [TEST 2] Testing Recursive Document Chunking ---")
    chunker = DocumentChunker(chunk_size=200, chunk_overlap=40)
    data_dir = config.SAMPLE_DOCS_DIR
    pdf_docs = DocumentLoader.load(data_dir / "cloud_computing_primer.pdf")

    chunks = chunker.split_documents(pdf_docs)
    assert len(chunks) > 2, f"Expected >2 chunks for 200-char chunking, got {len(chunks)}"
    first_chunk = chunks[0]
    assert "chunk_id" in first_chunk.metadata
    assert "page" in first_chunk.metadata
    assert "source" in first_chunk.metadata
    print(f"✓ Chunking passed: produced {len(chunks)} chunks with enriched metadata (Sample ID: {first_chunk.metadata['chunk_id']}).")


def test_ingestion_and_deduplication():
    print("\n--- [TEST 3] Testing Ingestion Pipeline & Deduplication ---")
    # Use clean test collection or standard collection
    store = ChromaVectorStore()
    store.clear_all()  # Clean slate for independent test

    pipeline = IngestionPipeline(vector_store=store, chunk_size=400, chunk_overlap=80)
    data_dir = config.SAMPLE_DOCS_DIR

    # Ingest TXT
    res_txt = pipeline.ingest(data_dir / "quantum_computing.txt")
    assert res_txt["status"] == "success", f"Ingestion failed: {res_txt}"
    initial_chunks = res_txt["total_chunks"]
    print(f"✓ Ingested TXT: {initial_chunks} chunks stored.")

    # Ingest TXT again (Duplicate test)
    res_dup = pipeline.ingest(data_dir / "quantum_computing.txt")
    assert res_dup["status"] == "skipped", f"Expected skipped duplicate, got {res_dup}"
    assert res_dup["reason"] == "duplicate"
    print("✓ Deduplication passed: duplicate document detected and skipped without redundant indexing.")

    # Ingest DOCX
    res_docx = pipeline.ingest(data_dir / "ai_ethics_guidelines.docx")
    assert res_docx["status"] == "success"
    print(f"✓ Ingested DOCX: {res_docx['total_chunks']} chunks stored.")

    # Ingest PDF
    res_pdf = pipeline.ingest(data_dir / "cloud_computing_primer.pdf")
    assert res_pdf["status"] == "success"
    assert res_pdf["total_pages"] == 2
    print(f"✓ Ingested PDF: {res_pdf['total_chunks']} chunks stored across {res_pdf['total_pages']} pages.")

    # Verify summary
    docs = store.get_indexed_documents()
    assert len(docs) == 3, f"Expected 3 indexed documents, got {len(docs)}"
    stats = store.get_stats()
    print(f"✓ Vector store stats: {stats['total_documents']} documents, {stats['total_chunks']} total chunks.")


def test_persistence():
    print("\n--- [TEST 4] Testing Vector Store Persistence Across Restarts ---")
    # Instantiate a completely new ChromaVectorStore instance simulating a restarted process
    reloaded_store = ChromaVectorStore()
    docs = reloaded_store.get_indexed_documents()
    stats = reloaded_store.get_stats()

    assert stats["total_documents"] == 3, f"Expected 3 persisted documents, got {stats['total_documents']}"
    assert stats["total_chunks"] > 0, f"Expected >0 chunks, got {stats['total_chunks']}"

    # Test retrieval from reloaded store
    results = reloaded_store.similarity_search_with_score("superposition and qubits", k=2)
    assert len(results) > 0, "No results retrieved from reloaded store!"
    top_doc, score = results[0]
    assert "qubit" in top_doc.page_content.lower() or "quantum" in top_doc.page_content.lower()
    print(f"✓ Persistence test passed: retrieved relevant chunk from persisted store (Score: {score:.4f}, Source: {top_doc.metadata.get('source')}).")


if __name__ == "__main__":
    print("========================================")
    print(" RUNNING INDEPENDENT INGESTION TESTS")
    print("========================================")
    test_document_loaders()
    test_chunking()
    test_ingestion_and_deduplication()
    test_persistence()
    print("\n>>> ALL INGESTION PIPELINE TESTS PASSED SUCCESSFULLY! <<<\n")
