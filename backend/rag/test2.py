# test_pipeline.py
import requests
from backend.rag.document_processor import DocumentProcessor
from backend.rag.vector_store import VectorStore


# ── Config ────────────────────────────────────────────────────────────────
PDF_URL = "https://arxiv.org/pdf/2412.19437"
TEST_PDF_PATH = "./test_deepseek.pdf"

# ── Download PDF ──────────────────────────────────────────────────────────
print("Downloading PDF...")
response = requests.get(PDF_URL)
with open(TEST_PDF_PATH, "wb") as f:
    f.write(response.content)
print(f"Downloaded {len(response.content) / 1024 / 1024:.1f} MB ✓")

# ── Process PDF ───────────────────────────────────────────────────────────
print("\nProcessing PDF...")
processor = DocumentProcessor()
document, pages = processor.process_pdf(TEST_PDF_PATH, source="arxiv")
print(f"Pages processed: {document.total_pages} ✓")

# ── Store in Weaviate ─────────────────────────────────────────────────────
print("\nStoring in Weaviate...")
store = VectorStore()
store.store_pages_batch(pages, document)
print(f"Stored {document.total_pages} pages ✓")

# ── Test queries ──────────────────────────────────────────────────────────
print("\n" + "="*50)
print("TESTING SEMANTIC SEARCH")
print("="*50)

queries = [
    "What is the architecture of DeepSeek-V3?",
    "How much did training cost in GPU hours?",
    "What is MLA multi head latent attention?",
    "What are the benchmark results?",
    "How does the MoE mixture of experts work?",
]

for query in queries:
    print(f"\nQuery: {query}")
    query_embedding = processor.embed_query(query)
    results = store.semantic_search(query_embedding, top_k=3)
    for i, result in enumerate(results):
        print(f"  Result {i+1}: page {result.page_number+1}/{document.total_pages}, score={result.score:.4f}")

# ── Summary ───────────────────────────────────────────────────────────────
print("\n" + "="*50)
print("SUMMARY")
print("="*50)
print(f"PDF: {document.filename}")
print(f"Total pages indexed: {document.total_pages}")
print(f"Model: athrael-soju/colqwen3.5-4.5B-v3")
print(f"MUVERA + SQ + HNSW: ✓")

# ── Cleanup ───────────────────────────────────────────────────────────────
store.close()
print("\nDone ✓")


'''RESULTS:'''
'''
Downloading PDF...
Downloaded 1.8 MB ✓

Processing PDF...
Pages processed: 53 ✓

Storing in Weaviate...
True
Stored 53 pages ✓

==================================================
TESTING SEMANTIC SEARCH
==================================================

Query: What is the architecture of DeepSeek-V3?
  Result 1: page 6/53, score=15.7804
  Result 2: page 7/53, score=15.4921
  Result 3: page 4/53, score=15.1597

Query: How much did training cost in GPU hours?
  Result 1: page 5/53, score=14.7277
  Result 2: page 26/53, score=12.6754
  Result 3: page 35/53, score=12.3765

Query: What is MLA multi head latent attention?
  Result 1: page 7/53, score=15.0186
  Result 2: page 2/53, score=13.5704
  Result 3: page 1/53, score=13.5536

Query: What are the benchmark results?
  Result 1: page 27/53, score=11.4775
  Result 2: page 1/53, score=11.4200
  Result 3: page 26/53, score=11.3440

Query: How does the MoE mixture of experts work?
  Result 1: page 48/53, score=14.2568
  Result 2: page 9/53, score=14.1545
  Result 3: page 10/53, score=13.7470

==================================================
SUMMARY
==================================================
PDF: test_deepseek.pdf
Total pages indexed: 53
Model: athrael-soju/colqwen3.5-4.5B-v3
MUVERA + SQ + HNSW: ✓

Done ✓
'''