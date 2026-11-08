# Newton School RAG Assignment - Docker, Qdrant & n8n

**Student Name**: Harshit Shukla  
**Roll Number**: 2102508751  
**Last 4 Digits**: 8751  
**Workflow Name**: `RAG_2102508751_Harshit_Shukla`  
**LLM Choice**: Google Gemini API  

---

## 📌 Project Overview
This repository contains the complete Dockerized Retrieval-Augmented Generation (RAG) system built with:
- **Qdrant Vector Database**: Running on port `6333` storing 3072-dimensional embeddings.
- **n8n Workflow Automation**: Running on port `5678` orchestrating both the Document Ingestion and Conversational AI Agent pipelines.
- **Google Gemini API**: Utilizing `gemini-embedding-001` for vector embeddings and `gemini-3.5-flash` for grounded, hallucination-resistant responses.

---

## 📂 Project Structure
```
├── docker-compose.yml                                # Qdrant and n8n container services
├── documents/
│   └── company_it_policy.txt                         # Policy document with personal proof code
├── workflows/
│   ├── RAG_2102508751_Harshit_Shukla_Ingestion.json  # Document ingestion & vector indexing workflow
│   └── RAG_2102508751_Harshit_Shukla_Chatbot.json    # RAG Chatbot workflow with vector tool & memory
├── RECORDING_GUIDE.md                                # Step-by-step video demonstration guide
└── README.md
```

---

## 🚀 Getting Started

### 1. Start Services
```bash
docker compose up -d
```
Verify containers are running:
```bash
docker ps
```

### 2. Access Dashboards
- **n8n Editor**: [http://localhost:5678](http://localhost:5678)
- **Qdrant Dashboard**: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

### 3. Workflows
- **Ingestion**: Ingests `company_it_policy.txt`, chunks text, generates embeddings, and indexes points into the `policy_documents` Qdrant collection.
- **Chatbot**: LangChain AI Agent with conversation buffer memory and vector search tool. Answers queries grounded strictly in policy documents and politely refuses unanswerable queries.

---

## 🔒 Verification & Proof
- **Personal Proof Sentence**:
  > *"The IT helpdesk code for Harshit Shukla (2102508751) is 8751."*
- **Test Prompt 1**: *"What is the IT helpdesk code for Harshit Shukla?"* $\rightarrow$ Returns `8751`.
- **Test Prompt 2**: *"What is the CEO's personal mobile phone number?"* $\rightarrow$ Refuses: *"I am sorry, but the provided documents do not contain information to answer this question."*
