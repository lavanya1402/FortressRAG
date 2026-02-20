## 🏗 Architecture Diagram

```mermaid
flowchart TB

subgraph Ingestion
A[Upload PDF] --> B[Chunking]
B --> C[Embedding]
C --> D[Store in FAISS]
end

subgraph Query
E[User Question] --> F[Embed Query]
F --> G[Top K Retrieval]
G --> H[Rerank Top N]
H --> I[LLM Answer]
end

D --> G
```
````

⚠ Important:

* Triple backticks + mermaid
* Exactly like above
* No extra space before ```mermaid

---

# 🎯 Aapke Repo ke liye Final Structure Should Be:

```
FortressRAG/
│
├── assets/
│   ├── rag_architecture.mmd
│   ├── rag_architecture.png
│   ├── First_Screenshot.png
│   ├── Second_Screenshot.png
│   ├── Third_Screenshot.png
│
├── streamlit_app.py
├── requirements.txt
└── README.md
```

---

# 📸 Screenshot Section Add Karo README me

```markdown
## 📸 Application Screenshots

### 1️⃣ Document Ingestion
![Ingestion](assets/First_Screenshot.png)

### 2️⃣ Query Interface
![Query](assets/Second_Screenshot.png)

### 3️⃣ Answer with Citations
![Answer](assets/Third_Screenshot.png)
```


---


