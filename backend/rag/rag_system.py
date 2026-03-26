import ollama
import base64
from PIL import Image
from io import BytesIO
from weaviate.classes.query import Filter
from backend.models import SearchResult, Message
from backend.rag.document_processor import DocumentProcessor
from backend.rag.vector_store import VectorStore
from backend.config import OLLAMA_MODEL


class RAGSystem:
    def __init__(self):
        self.processor = DocumentProcessor()
        self.store = VectorStore()
        self.system_prompt = """You are a helpful teaching assistant.
You answer questions based strictly on the provided course material pages.
If the answer is not in the provided pages, say so clearly.
Always be concise, accurate and educational."""

    # ─── Encode images for Ollama ─────────────────────────────────────────

    def _encode_images(self, results: list[SearchResult]) -> list[str]:
        encoded = []
        for result in results:
            with open(result.image_path, "rb") as f:
                encoded.append(base64.b64encode(f.read()).decode())
        return encoded

    # ─── Build prompt ─────────────────────────────────────────────────────

    def _build_prompt(
        self,
        query: str,
        results: list[SearchResult]
    ) -> str:
        context = "\n".join([
            f"[Page {i+1}] doc: {r.doc_id}, page: {r.page_number}, source: {r.source}"
            for i, r in enumerate(results)
        ])
        return f"""Based on the following course material pages:
{context}

Answer this question: {query}"""

    # ─── Core query ───────────────────────────────────────────────────────

    def query(
        self,
        query: str,
        conversation_history: list[Message] = None,
        top_k: int = 3,
        filters: Filter = None,
    ) -> str:
        # 1. embed query
        query_embedding = self.processor.embed_query(query)

        # 2. retrieve relevant pages
        results = self.store.semantic_search(
            query_embedding=query_embedding,
            top_k=top_k,
            filters=filters
        )

        if not results:
            return "No relevant pages found in the course material."

        # 3. build messages
        messages = [{"role": "system", "content": self.system_prompt}]

        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })

        messages.append({
            "role": "user",
            "content": self._build_prompt(query, results),
            "images": self._encode_images(results)
        })

        # 4. generate
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={"num_predict": 512}
        )
        return response["message"]["content"]

    # ─── Exam generation ──────────────────────────────────────────────────

    def generate_exam(
        self,
        topic: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        filters: Filter = None
    ) -> str:
        query_embedding = self.processor.embed_query(topic)
        results = self.store.semantic_search(
            query_embedding=query_embedding,
            top_k=5,
            filters=filters
        )

        if not results:
            return "No relevant pages found for exam generation."

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": f"""Generate {num_questions} {difficulty} difficulty exam questions
based strictly on the provided course material pages.
Format each as:
Q[n]: [question]
A: [answer]""",
                "images": self._encode_images(results)
            }
        ]

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={"num_predict": 1024}
        )
        return response["message"]["content"]

    # ─── Exercise generation ──────────────────────────────────────────────

    def generate_exercises(
        self,
        topic: str,
        exercise_type: str = "practice",
        filters: Filter = None
    ) -> str:
        query_embedding = self.processor.embed_query(topic)
        results = self.store.semantic_search(
            query_embedding=query_embedding,
            top_k=5,
            filters=filters
        )

        if not results:
            return "No relevant pages found for exercise generation."

        messages = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": f"""Generate {exercise_type} exercises based strictly
on the provided course material pages.
Include clear instructions and progressive difficulty.""",
                "images": self._encode_images(results)
            }
        ]

        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=messages,
            options={"num_predict": 1024}
        )
        return response["message"]["content"]

    def close(self):
        self.processor.close()
        self.store.close()