import uuid
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path
from backend.models import Page, Document
from backend.config import PAGES_STORAGE_PATH
from backend.rag.colqwen_embedder import process_docs_remote, process_query_remote


class DocumentProcessor:
    def __init__(self):
        Path(PAGES_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

    # ─── PDF to images ────────────────────────────────────────────────────

    def pdf_to_images(self, pdf_path: str) -> list[Image.Image]:
        return convert_from_path(pdf_path, dpi=185)

    # ─── Save page image ──────────────────────────────────────────────────

    def save_page_image(
        self,
        image: Image.Image,
        doc_id: str,
        page_number: int
    ) -> str:
        image_path = f"{PAGES_STORAGE_PATH}/{doc_id}_page_{page_number}.png"
        image.save(image_path)
        return image_path

    # ─── Embed pages (batched) ────────────────────────────────────────────

    def embed_pages(self, images: list[Image.Image], batch_size: int = 20) -> list:
        all_embeddings = []
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            embeddings = process_docs_remote(batch)
            all_embeddings.extend(embeddings)
        return all_embeddings

    # ─── Embed query ──────────────────────────────────────────────────────

    def embed_query(self, query: str) -> list:
        return process_query_remote(query)

    def close(self):
        pass  # remote embedder — no persistent connection to close

    # ─── Process full PDF ─────────────────────────────────────────────────

    def process_pdf(
        self,
        pdf_path: str,
        source: str = "local",
        doc_id: str = None,
    ) -> tuple[Document, list[Page]]:
        doc_id = doc_id or str(uuid.uuid4())
        filename = Path(pdf_path).name
        images = self.pdf_to_images(pdf_path)
        embeddings = self.embed_pages(images)

        document = Document(
            doc_id=doc_id,
            filename=filename,
            source=source,
            total_pages=len(images)
        )

        pages = []
        for i, (image, embedding) in enumerate(zip(images, embeddings)):
            image_path = self.save_page_image(image, doc_id, i)
            pages.append(Page(
                doc_id=doc_id,
                page_number=i,
                image_path=image_path,
                source=source,
                embedding=embedding,
            ))

        return document, pages