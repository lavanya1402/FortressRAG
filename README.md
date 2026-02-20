# 📦 FortressRAG

### 🔐 Enterprise-Grade Hybrid Retrieval-Augmented Generation System

FortressRAG is a modular, production-oriented **Hybrid RAG (Retrieval-Augmented Generation)** framework designed for secure, scalable, and enterprise-ready LLM applications.

It combines **Vector Search (FAISS)** with intelligent chunking, optional reranking, and structured generation to deliver reliable responses from PDF documents.

---

# 🖼️ Application Screenshots

> Make sure images are inside `/assets` folder

```markdown
![App Screenshot 1](assets/First_Screenshot%20.png)
![App Screenshot 2](assets/Second_Screenshot%20.png)
![App Screenshot 3](assets/Third_Screenshot%20.png)
```

⚠️ IMPORTANT:
Tumhare file names me space hai (`First_Screenshot .png`)
Either:

* Rename files to `First_Screenshot.png` (recommended)
  OR
* Use `%20` encoding as shown above.

Recommended rename:

```
First_Screenshot.png
Second_Screenshot.png
Third_Screenshot.png
```

Then use:

```markdown
![App Screenshot 1](assets/First_Screenshot.png)
![App Screenshot 2](assets/Second_Screenshot.png)
![App Screenshot 3](assets/Third_Screenshot.png)
```

---

# 🏗️ Architecture Diagram (Mermaid Markdown)

GitHub automatically renders Mermaid if wrapped in ```mermaid block.

Copy this:

````markdown
## 🏗️ System Architecture

```mermaid
flowchart TB

subgraph Ingestion
A[Upload PDF] --> B[Chunking]
B --> C[Embedding Generation]
C --> D[Store in FAISS]
end

subgraph Query
E[User Question] --> F[Embed Query]
F --> G[Vector Retrieval]
G --> H[Reranker Optional]
H --> I[LLM Generation]
end

D --> G
I --> J[Final Answer]
````

````

---

# 📂 Project Structure

```markdown
````

FortressRAG/
│
├── app/
│   ├── api.py
│   ├── config.py
│   ├── embedding.py
│   ├── generation.py
│   ├── ingestion.py
│   ├── reranker.py
│   ├── retrieval.py
│   └── tenancy.py
│
├── assets/
├── docs/
├── storage/
│
├── main.py
├── streamlit_app.py
├── rag_test.py
├── requirements.txt
└── .gitignore

```
```

---

# 🚀 Features

* Hybrid Retrieval Architecture
* FAISS Vector Index
* Intelligent Chunking
* Modular Enterprise Codebase
* Streamlit Interface
* Secure Environment Configuration
* Multi-Tenant Ready

---

# ▶️ Run Application

```bash
streamlit run streamlit_app.py
```

---

# 🔐 Environment Setup

Create `.env`:

```
OPENAI_API_KEY=your_api_key_here
```

---

# 🛡️ Design Philosophy

FortressRAG is built for:

* Production scalability
* Modular extension
* Secure deployment
* Enterprise-grade AI systems

---



