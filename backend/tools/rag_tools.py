from langchain.tools import tool
from backend.config import TOP_K_RETRIEVAL

@tool
def search_course_material(query: str) -> str:
    """Search course material for relevant information.
    Use this when the teacher asks about course content,
    wants to find specific topics, or needs information
    from uploaded PDFs."""
    try:
        from backend.rag.rag_system import RAGSystem
        rag = RAGSystem()
        result = rag.query(query, top_k=TOP_K_RETRIEVAL)
        rag.close()
        return result
    except Exception as e:
        return f"RAG search failed: {str(e)}"

@tool
def generate_exam_from_material(
    topic: str,
    num_questions: int = 5,
    difficulty: str = "medium"
) -> str:
    """Generate exam questions from course material.
    Use this when the teacher asks to create an exam,
    quiz or test based on uploaded course content."""
    try:
        from backend.rag.rag_system import RAGSystem
        rag = RAGSystem()
        result = rag.generate_exam(
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty
        )
        rag.close()
        return result
    except Exception as e:
        return f"Exam generation failed: {str(e)}"

@tool
def generate_exercises_from_material(
    topic: str,
    exercise_type: str = "practice"
) -> str:
    """Generate exercises from course material.
    Use this when the teacher asks to create practice
    exercises or homework based on uploaded course content."""
    try:
        from backend.rag.rag_system import RAGSystem
        rag = RAGSystem()
        result = rag.generate_exercises(
            topic=topic,
            exercise_type=exercise_type
        )
        rag.close()
        return result
    except Exception as e:
        return f"Exercise generation failed: {str(e)}"

@tool
def upload_pdf_to_platform(pdf_path: str, source: str = "local") -> str:
    """Upload and index a PDF to the platform course material.
    Use this when the teacher wants to add a new course document
    or lecture notes so students can search it."""
    try:
        import os
        from backend.rag.document_processor import DocumentProcessor
        from backend.rag.vector_store import VectorStore

        if not os.path.exists(pdf_path):
            return f"File not found: {pdf_path}"

        processor = DocumentProcessor()
        store = VectorStore()

        document, pages = processor.process_pdf(pdf_path, source=source)
        store.store_pages_batch(pages, document)

        processor.close()
        store.close()

        return f"Successfully uploaded '{document.filename}' — {document.total_pages} pages indexed."
    except Exception as e:
        return f"PDF upload failed: {str(e)}"