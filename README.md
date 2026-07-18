# AI Financial Research Assistant

Ask questions about company annual reports in natural language, with cited
page numbers. RAG pipeline: PDF → chunks → OpenAI embeddings → ChromaDB →
retrieval → LLM answer with citations. Streamlit UI.

> 🚧 Work in progress — full README (architecture diagram, eval results,
> screenshots) lands at milestone 6.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env   # then put your OpenAI API key in .env
streamlit run app.py
```
