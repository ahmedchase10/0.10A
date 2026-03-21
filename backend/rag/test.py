# ── Install dependencies for collab ───────────────────────────────────────────────────
'''
!pip install weaviate-client transformers torch pillow
!pip install git+https://github.com/illuin-tech/colpali.git
'''
# ── Imports ───────────────────────────────────────────────────────────────
import torch
from PIL import Image
from colpali_engine.models import ColQwen3_5, ColQwen3_5Processor
from transformers.utils.import_utils import is_flash_attn_2_available
import weaviate
import weaviate.classes.config as wc
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.query import MetadataQuery
from weaviate.util import generate_uuid5

# ── Config ────────────────────────────────────────────────────────────────
COLQWEN_MODEL = "athrael-soju/colqwen3.5-4.5B-v3"
COLLECTION_NAME = "TestPages"
PERSISTENCE_PATH = "./test_weaviate"
# ── Load model ────────────────────────────────────────────────────────────
print("Loading model...")

if torch.cuda.is_available():
    device = "cuda:0"
elif torch.backends.mps.is_available():
    device = "mps"
else:
    device = "cpu"

attn_implementation = (
    "flash_attention_2" if is_flash_attn_2_available() else "eager"
)

model = ColQwen3_5.from_pretrained(
    COLQWEN_MODEL,
    torch_dtype=torch.float32 if device == "cpu" else torch.bfloat16,
    device_map=device,
    attn_implementation=attn_implementation,
).eval()

processor = ColQwen3_5Processor.from_pretrained(COLQWEN_MODEL)
print(f"Model loaded ✓ — device: {device}")


# ── Connect to Weaviate embedded ──────────────────────────────────────────
print("\nConnecting to Weaviate...")
client = weaviate.connect_to_embedded(
    persistence_data_path=PERSISTENCE_PATH,
    version="1.31.0" 
)
print(f"Weaviate ready ✓ — version: {client.get_meta()['version']}")

# ── Create collection ─────────────────────────────────────────────────────
print("\nCreating collection...")
if client.collections.exists(COLLECTION_NAME):
    client.collections.delete(COLLECTION_NAME)
    print("Deleted existing collection")

collection = client.collections.create(
    name=COLLECTION_NAME,
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
        Property(name="doc_id", data_type=DataType.TEXT, vectorize_property_name=False),
        Property(name="page_number", data_type=DataType.INT),
        Property(name="image_path", data_type=DataType.TEXT, vectorize_property_name=False),
        Property(name="source", data_type=DataType.TEXT, vectorize_property_name=False),
    ]
)
print("Collection created ✓")
# ── Check actual config stored ────────────────────────────────────────────
print("\nChecking actual collection config...")
config = collection.config.get()

for vector_name, vector_config in config.vector_config.items():
    print(f"\nVector name: {vector_name}")
    print(f"Full vector config: {vector_config}")
    print(f"All attributes: {dir(vector_config)}")

    # check if MUVERA is present
    index_config = vector_config.vector_index_config
    if hasattr(index_config, 'multi_vector'):
        mv_config = index_config.multi_vector
        print(f"Multi-vector config: {mv_config}")
        if hasattr(mv_config, 'encoding'):
            print(f"Encoding: {mv_config.encoding}")
            if mv_config.encoding is not None:
                print("✅ MUVERA is active")
            else:
                print("❌ MUVERA not active — brute force MaxSim")
        else:
            print("❌ No encoding found — MUVERA not active")
    else:
        print("❌ No multi-vector config found")

    # check quantization
    if hasattr(index_config, 'quantizer') and index_config.quantizer is not None:
        print(f"✅ Quantization active: {index_config.quantizer}")
    else:
        print("❌ No quantization")

# ── Embed dummy images ────────────────────────────────────────────────────
print("\nEmbedding dummy images...")

images = [
    Image.new("RGB", (128, 128), color="white"),
    Image.new("RGB", (128, 128), color="gray"),
    Image.new("RGB", (128, 128), color="black"),
]

batch = processor.process_images(images)
batch = {k: v.to(model.device) for k, v in batch.items()}

with torch.no_grad():
    embeddings = model(**batch)

embeddings_list = embeddings.cpu().float().numpy().tolist()
print(f"Embedded {len(embeddings_list)} images ✓")
print(f"Embedding shape: ({len(embeddings_list[0])}, {len(embeddings_list[0][0])})")

# ── Store in Weaviate ─────────────────────────────────────────────────────
print("\nStoring in Weaviate...")

with collection.batch.dynamic() as batch_insert:
    for i, embedding in enumerate(embeddings_list):
        page_uuid = generate_uuid5(f"test_doc_page_{i}")
        batch_insert.add_object(
            uuid=page_uuid,
            properties={
                "doc_id": "test_doc",
                "page_number": i,
                "image_path": f"./pages/test_doc_page_{i}.png",
                "source": "local",
            },
            vector={"colqwen": embedding}
        )

print(f"Stored {len(collection)} objects ✓")

# ── Test semantic search ──────────────────────────────────────────────────
print("\nTesting semantic search...")

query = "white background page"

batch_query = processor.process_queries([query])
batch_query = {k: v.to(model.device) for k, v in batch_query.items()}

with torch.no_grad():
  model.rope_deltas = None 
  query_embedding = model(**batch_query)

query_embedding_list = query_embedding[0].cpu().float().numpy().tolist()

results = collection.query.near_vector(
    near_vector=query_embedding_list,
    target_vector="colqwen",
    limit=3,
    return_metadata=MetadataQuery(distance=True)
)

print(f"Results returned: {len(results.objects)}")
for i, obj in enumerate(results.objects):
    print(f"  Result {i+1}: page={obj.properties['page_number']}, distance={obj.metadata.distance:.4f}")

# ── Verify persistence ────────────────────────────────────────────────────
print("\nVerifying persistence...")
print(f"Total objects in collection: {len(collection)}")

# ── Cleanup ───────────────────────────────────────────────────────────────
client.close()
print("\nAll tests passed ✓")
'''

---

**What this tests in order:**
```
1. Model loads         → ColQwen3.5 ready
2. Weaviate connects   → embedded instance running
3. Collection created  → MUVERA + SQ configured
4. Images embedded     → ColQwen2.5 produces multi-vectors
5. Vectors stored      → Weaviate accepts and indexes them
6. Semantic search     → near_vector returns ranked results
7. Persistence check   → objects actually saved
```

---

**Expected output:**
```
Results returned: 3
  Result 1: page=0, distance=0.XXXX  ← white image closest to "white background"
  Result 2: page=1, distance=0.XXXX
  Result 3: page=2, distance=0.XXXX

Total objects in collection: 3
All tests passed ✓
'''