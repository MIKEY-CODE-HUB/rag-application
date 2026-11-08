# Newton School RAG Assignment - Video Recording & Submission Guide

**Student Name**: Harshit Shukla  
**Roll Number**: 2102508751  
**Last 4 Digits**: 8751  
**Workflow Name**: `RAG_2102508751_Harshit_Shukla`  
**LLM Choice**: Google Gemini API  

---

## 📁 Prepared Project Files
All required files are ready inside `/Users/mikey/newton-rag-n8n/`:
1. `docker-compose.yml`: Pre-configured for Qdrant (`6333`) and n8n (`5678`). Images are already downloaded!
2. `documents/company_it_policy.txt`: Policy document containing your personal proof:
   > *"The IT helpdesk code for Harshit Shukla (2102508751) is 8751."*
3. `workflows/RAG_2102508751_Harshit_Shukla_Ingestion.json`: Ready to import Ingestion Workflow.
4. `workflows/RAG_2102508751_Harshit_Shukla_Chatbot.json`: Ready to import Chatbot Workflow.

---

## 🎬 Video Recording Instructions (One Continuous Take)
*Do not make any cuts, edits, or trimming. Make sure the macOS system clock in the top-right menu bar remains visible throughout.*

### Step 1: Docker Desktop
1. Open **Docker Desktop**.
2. Clearly show your **signed-in email ID** in the top-right corner on screen.
   *(Mandatory rule: If your email ID is not visible, you will receive 0 marks).*

### Step 2: Terminal Execution
1. Open your **Terminal** app.
2. Run:
   ```bash
   date
   ```
3. Run:
   ```bash
   docker ps
   ```
   *(Shows zero active containers initially)*.
4. Start your required containers by running:
   ```bash
   cd ~/newton-rag-n8n && docker compose start
   ```
   *(or `docker compose up -d`)*
5. Run:
   ```bash
   docker ps
   ```
   *(Now clearly shows both `n8n` and `qdrant` running)*.

### Step 3: Open n8n & Configure Credentials
1. In your web browser, open:
   [http://localhost:5678](http://localhost:5678)
2. If opening for the first time, set up your local n8n account (Name, Email, Password).
3. Set up two credentials in **Credentials** (sidebar):
   - **Qdrant API**:
     - Host: `qdrant` (or `http://localhost:6333`)
     - Port: `6333`
     - API Key: leave empty
   - **Google Gemini API**:
     - Enter your Gemini API Key.

### Step 4: Ingestion Pipeline Execution
1. In n8n, create or import the workflow from:
   `/Users/mikey/newton-rag-n8n/workflows/RAG_2102508751_Harshit_Shukla_Ingestion.json`
2. Ensure the workflow name at the top is: `RAG_2102508751_Harshit_Shukla`.
3. Click **"Test workflow"** (or execute).
4. Show green checkmarks on all nodes.
5. Switch to a new browser tab and open **Qdrant Dashboard**:
   [http://localhost:6333/dashboard](http://localhost:6333/dashboard)
6. Click on **Collections** -> show `policy_documents` with vectors populated on screen.

### Step 5: Chatbot Pipeline Execution & Personal Proof
1. Switch back to n8n and open your Chatbot workflow:
   `RAG_2102508751_Harshit_Shukla` (imported from `workflows/RAG_2102508751_Harshit_Shukla_Chatbot.json`).
2. Click **"Chat"** at the bottom / **Test workflow**.
3. **Prompt 1 (Mandatory Personal Proof)**:
   Ask:
   > `What is the IT helpdesk code for Harshit Shukla?`
   
   Show the chatbot responding clearly with:
   > *"The IT helpdesk code for Harshit Shukla (2102508751) is 8751."*
4. **Prompt 2 (Refusal Check)**:
   Ask:
   > `What is the CEO's personal mobile phone number?`
   
   Show the chatbot appropriately refusing:
   > *"I am sorry, but the provided documents do not contain information to answer this question."*

---

## 📤 Submission Checklist
1. **Stop screen recording** (save MP4/MOV file).
2. **Export Workflows**:
   In n8n, click the three dots (`...`) in the top-right -> **Export** -> Save JSON.
3. **Google Drive Upload**:
   - Upload video to Google Drive.
   - Sharing settings: Set to **Restricted**.
   - Share explicitly with:
     - `mahfooj.ali@newtonschool.co` (Viewer)
     - `venkata.edupuganti@newtonschool.co` (Viewer)
4. **Submit Form**:
   - Link: [Google Form Submission](https://docs.google.com/forms/d/e/1FAIpQLScyAxUpEKWSYBCr7VhOetX_Gqf7E2SPK5P0yb-6Ab3mLSsNcQ/viewform?usp=dialog)
   - Paste your Google Drive video link.
   - Upload the exported workflow JSON files.
