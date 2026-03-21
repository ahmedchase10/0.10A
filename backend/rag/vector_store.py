import weaviate
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery, Filter
from weaviate.util import generate_uuid5
from backend.models import Page, Document, SearchResult
from backend.config import (
    WEAVIATE_PERSISTENCE_PATH,
    WEAVIATE_COLLECTION,
    WEAVIATE_VERSION
)


class VectorStore:
    def __init__(self):
        self.client = weaviate.connect_to_embedded(
            persistence_data_path=WEAVIATE_PERSISTENCE_PATH,
            version=WEAVIATE_VERSION

        )
        self.collection = self._get_or_create_collection()

    # ─── Collection setup ─────────────────────────────────────────────────

    def _get_or_create_collection(self):
        if not self.client.collections.exists(WEAVIATE_COLLECTION):
            return self.client.collections.create(
                name=WEAVIATE_COLLECTION,
                vector_config=[
                    Configure.MultiVectors.self_provided(
                        name="colqwen",
                        encoding=Configure.VectorIndex.MultiVector.Encoding.muvera(),
                        vector_index_config=Configure.VectorIndex.hnsw(
                            multi_vector=Configure.VectorIndex.MultiVector.multi_vector(),
                            quantizer=Configure.VectorIndex.Quantizer.sq()
                        )
                    )
                ],
                properties=[
                    Property(
                        name="doc_id",
                        data_type=DataType.TEXT,
                        vectorize_property_name=False
                    ),
                    Property(
                        name="filename",
                        data_type=DataType.TEXT,
                        vectorize_property_name=False
                    ),
                    Property(
                        name="page_number",
                        data_type=DataType.INT,
                    ),
                    Property(
                        name="image_path",
                        data_type=DataType.TEXT,
                        vectorize_property_name=False
                    ),
                    Property(
                        name="source",
                        data_type=DataType.TEXT,
                        vectorize_property_name=False
                    ),
                    Property(
                        name="total_pages",
                        data_type=DataType.INT,
                    ),
                    Property(
                        name="content_description",
                        data_type=DataType.TEXT,
                        vectorize_property_name=True
                    ),
                ]
            )
        return self.client.collections.get(WEAVIATE_COLLECTION)

    # ─── Store ────────────────────────────────────────────────────────────

    def store_page(self, page: Page, document: Document):
        page_uuid = generate_uuid5(f"{page.doc_id}_{page.page_number}")
        self.collection.data.insert(
            uuid=page_uuid,
            properties={
                "doc_id": page.doc_id,
                "filename": document.filename,
                "page_number": page.page_number,
                "image_path": page.image_path,
                "source": page.source,
                "total_pages": document.total_pages,
                "content_description": page.content_description or "",
            },
            vector={"colqwen": page.embedding}
        )
        return page_uuid

    def store_pages_batch(self, pages: list[Page], document: Document):
        with self.collection.batch.dynamic() as batch:
            for page in pages:
                page_uuid = generate_uuid5(
                    f"{page.doc_id}_{page.page_number}"
                )
                batch.add_object(
                    uuid=page_uuid,
                    properties={
                        "doc_id": page.doc_id,
                        "filename": document.filename,
                        "page_number": page.page_number,
                        "image_path": page.image_path,
                        "source": page.source,
                        "total_pages": document.total_pages,
                        "content_description": page.content_description or "",
                    },
                    vector={"colqwen": page.embedding}
                )

        if self.collection.batch.failed_objects:
            print(f"Failed: {len(self.collection.batch.failed_objects)}")

    # ─── Search ───────────────────────────────────────────────────────────

    def semantic_search(self,query_embedding: list,top_k: int = 5,filters: Filter = None) -> list[SearchResult]:
        results = self.collection.query.near_vector(
            near_vector=query_embedding,  # ← raw multi-vector directly
            target_vector="colqwen",  # ← named vector name
            limit=top_k,
            filters=filters,
            return_metadata=MetadataQuery(distance=True)
        )
        return self._to_search_results(results)
    """bm25_and hybrid are only here for text files implementation afterwards """

    def bm25_search(self,query: str,top_k: int = 5,filters: Filter = None) -> list[SearchResult]:
        results = self.collection.query.bm25(
            query=query,
            query_properties=["content_description"],
            limit=top_k,
            filters=filters,
            return_metadata=MetadataQuery(score=True)
        )
        return self._to_search_results(results)

    def hybrid_search(self,query: str,query_embedding: list,top_k: int = 5,alpha: float = 0.75,filters: Filter = None) -> list[SearchResult]:
        results = self.collection.query.hybrid(
            query=query,
            vector=query_embedding,  # ← raw multi-vector directly
            target_vector="colqwen",  # ← named vector name
            alpha=alpha,
            query_properties=["content_description"],
            limit=top_k,
            filters=filters,
            return_metadata=MetadataQuery(score=True)
        )
        return self._to_search_results(results)


    def filter_search(self,filters: Filter = None,top_k: int = 5) -> list[SearchResult]:
        results = self.collection.query.fetch_objects(
            limit=top_k,
            filters=filters,
        )
        return self._to_search_results(results)

    # ─── Helper ───────────────────────────────────────────────────────────

    def _to_search_results(self, results) -> list[SearchResult]:
        return [
            SearchResult(
                doc_id=obj.properties["doc_id"],
                page_number=obj.properties["page_number"],
                image_path=obj.properties["image_path"],
                source=obj.properties["source"],
                score=(
                    -obj.metadata.distance
                    if obj.metadata and obj.metadata.distance
                    else obj.metadata.score
                    if obj.metadata and obj.metadata.score
                    else 0.0
                )
            )
            for obj in results.objects
        ]

    def close(self):
        self.client.close()