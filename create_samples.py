import os
from pathlib import Path
from docx import Document as DocxDocument
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

data_dir = Path("/Users/mikey/rag-application/data/sample_docs")
data_dir.mkdir(parents=True, exist_ok=True)

# 1. Create sample TXT file
txt_path = data_dir / "quantum_computing.txt"
txt_content = """# Quantum Computing Overview

Quantum computing is a rapidly-emerging technology that harnesses the laws of quantum mechanics to solve problems too complex for classical computers.
Classical computers use bits that represent either 0 or 1.
In contrast, quantum computers use qubits which can exist in a state of superposition.
Superposition allows qubits to be in a combination of 0 and 1 simultaneously.
Another key principle is entanglement, where quantum particles become inextricably linked regardless of distance.
Key quantum algorithms include Shor's algorithm for prime factorization and Grover's algorithm for unstructured database search.
Leading companies investing in quantum hardware include Google, IBM, Rigetti, and IonQ.
Cryogenic refrigeration systems are used to maintain superconducting qubits at near absolute zero temperatures.
"""
with open(txt_path, "w", encoding="utf-8") as f:
    f.write(txt_content)
print(f"Created TXT: {txt_path}")

# 2. Create sample DOCX file
docx_path = data_dir / "ai_ethics_guidelines.docx"
doc = DocxDocument()
doc.add_heading("AI Ethics and Governance Framework", level=0)
doc.add_paragraph("This document outlines organizational principles for responsible artificial intelligence deployment.")
doc.add_heading("Core Principles", level=1)
doc.add_paragraph("1. Transparency: AI systems must provide explainable rationales for high-stakes decisions.")
doc.add_paragraph("2. Fairness and Non-discrimination: Algorithms must be audited periodically to detect algorithmic bias against protected groups.")
doc.add_paragraph("3. Privacy and Data Security: User data must be encrypted at rest and in transit, following GDPR and CCPA standards.")
doc.add_paragraph("4. Accountability: Human oversight must be maintained through a human-in-the-loop mechanism.")

table = doc.add_table(rows=1, cols=3)
hdr_cells = table.rows[0].cells
hdr_cells[0].text = "Risk Level"
hdr_cells[1].text = "Category"
hdr_cells[2].text = "Required Action"

row_cells = table.add_row().cells
row_cells[0].text = "High"
row_cells[1].text = "Autonomous Medical Diagnosis"
row_cells[2].text = "Mandatory Clinical Validation & Human Sign-off"

doc.save(docx_path)
print(f"Created DOCX: {docx_path}")

# 3. Create sample multi-page PDF file
pdf_path = data_dir / "cloud_computing_primer.pdf"
c = canvas.Canvas(str(pdf_path), pagesize=letter)

# Page 1
c.setFont("Helvetica-Bold", 16)
c.drawString(72, 750, "Cloud Computing Architecture Primer - Page 1")
c.setFont("Helvetica", 12)
c.drawString(72, 710, "Cloud computing is the on-demand delivery of IT resources over the internet.")
c.drawString(72, 690, "Primary service models include IaaS (Infrastructure as a Service), PaaS, and SaaS.")
c.drawString(72, 670, "IaaS provides fundamental compute, storage, and networking capabilities like Amazon EC2.")
c.drawString(72, 650, "PaaS provides managed development environments such as Google App Engine.")
c.drawString(72, 630, "SaaS provides ready-to-use software applications like Google Workspace and Salesforce.")
c.showPage()

# Page 2
c.setFont("Helvetica-Bold", 16)
c.drawString(72, 750, "Cloud Computing Architecture Primer - Page 2")
c.setFont("Helvetica", 12)
c.drawString(72, 710, "Cloud Deployment Models and Reliability:")
c.drawString(72, 690, "Public clouds are operated by third-party providers such as AWS, Google Cloud, and Azure.")
c.drawString(72, 670, "Private clouds are infrastructure operated solely for a single organization.")
c.drawString(72, 650, "Hybrid clouds combine public and private environments with data orchestration.")
c.drawString(72, 630, "Multi-region deployments ensure high availability with 99.999 percent uptime SLA guarantees.")
c.drawString(72, 610, "Auto-scaling groups dynamically adjust virtual machine counts based on CPU utilization metrics.")
c.showPage()

c.save()
print(f"Created PDF: {pdf_path}")
