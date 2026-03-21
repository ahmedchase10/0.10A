import torch
import uuid
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path
from colpali_engine.models import ColQwen2_5, ColQwen2_5_Processor
from transformers.utils.import_utils import is_flash_attn_2_available
from backend.models import Page, Document
from backend.config import (
    COLQWEN_MODEL,
    PAGES_STORAGE_PATH,
)



class DocumentProcessor:
    def __init__(self):
        if torch.cuda.is_available():
            self.device = "cuda:0"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"

        self.attn_implementation = (
            "flash_attention_2" if is_flash_attn_2_available() else "eager"
        )

        self.model = ColQwen2_5.from_pretrained(
            COLQWEN_MODEL,
            torch_dtype=torch.float32 if self.device == "cpu" else torch.bfloat16,
            device_map=self.device,
            attn_implementation=self.attn_implementation,  # ← add here
        ).eval()
        self.processor = ColQwen2_5_Processor.from_pretrained(COLQWEN_MODEL)

        Path(PAGES_STORAGE_PATH).mkdir(parents=True, exist_ok=True)

    # ─── PDF to images ────────────────────────────────────────────────────

    def pdf_to_images(self, pdf_path: str) -> list[Image.Image]:
        return convert_from_path(pdf_path)

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

    # ─── Embed pages (full batch) ─────────────────────────────────────────

    def embed_pages(self, images: list[Image.Image]) -> list:
        batch = self.processor.process_images(images)
        batch = {k: v.to(self.model.device) for k, v in batch.items()}
        with torch.no_grad():
            embeddings = self.model(**batch)
        return embeddings.cpu().float().numpy().tolist()

    # ─── Embed query ──────────────────────────────────────────────────────

    def embed_query(self, query: str) -> list:
        batch = self.processor.process_queries([query])
        batch = {k: v.to(self.model.device) for k, v in batch.items()}
        with torch.no_grad():
            self.model.rope_deltas = None  # ← required for ColQwen3.5
            embeddings = self.model(**batch)
        return embeddings[0].cpu().float().numpy().tolist()

    # ─── Process full PDF ─────────────────────────────────────────────────

    def process_pdf(
        self,
        pdf_path: str,
        source: str = "local"
    ) -> tuple[Document, list[Page]]:
        doc_id = str(uuid.uuid4())
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

    def close(self):
        del self.model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()