import modal
import torch
import base64
from io import BytesIO
from PIL import Image

app = modal.App("colqwen-api")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("git")
    .pip_install([
        "torch",
        "Pillow",
        "transformers",
        "fastapi[standard]"
    ])
    .pip_install([
        "git+https://github.com/illuin-tech/colpali.git"
    ])
)
#cpu and ram will be added to enhance performance
@app.cls(
    gpu="l4",
    cpu=2.0,
    memory=2048,
    image=image,
    secrets=[modal.Secret.from_name("digi_school")],
    scaledown_window=300,
)
class ColQwenEmbedder:

    @modal.enter()
    def load_model(self):
        from colpali_engine.models import ColQwen3_5, ColQwen3_5Processor


        self.device = "cuda:0"
        attn = "sdpa"

        self.model = ColQwen3_5.from_pretrained(
            "athrael-soju/colqwen3.5-4.5B-v3",
            torch_dtype=torch.float16,
            device_map=self.device,
            attn_implementation=attn,
        ).eval()

        self.processor = ColQwen3_5Processor.from_pretrained(
            "athrael-soju/colqwen3.5-4.5B-v3"
        )
        print(f"Device: {self.device}")
        print(f"dtype: {self.model.dtype}")
        print(f"GPU memory: {torch.cuda.memory_allocated() / 1024 ** 3:.1f} GB used")

    def _check_auth(self, api_key: str):
        import os
        if api_key != os.environ["DIGI_TOKEN"]:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Unauthorized")

    @modal.fastapi_endpoint(method="POST")
    def encode_docs(self, payload: dict):
        self._check_auth(payload.get("api_key", ""))

        images = []
        for b64 in payload["images"]:
            img_bytes = base64.b64decode(b64)
            img = Image.open(BytesIO(img_bytes)).convert("RGB")
            images.append(img)

        print(f"After decoding images: {torch.cuda.memory_allocated() / 1024 ** 3:.1f} GB")

        batch = self.processor.process_images(images)
        batch = {k: v.to(self.model.device) for k, v in batch.items()}

        print(f"After processing batch: {torch.cuda.memory_allocated() / 1024 ** 3:.1f} GB")

        with torch.no_grad():
            embeddings = self.model(**batch)

        print(f"After inference: {torch.cuda.memory_allocated() / 1024 ** 3:.1f} GB")
        torch.cuda.empty_cache()

        return {"vectors": embeddings.detach().cpu().float().numpy().tolist()}



    @modal.fastapi_endpoint(method="POST")
    def encode_query(self, payload: dict):
        self._check_auth(payload.get("api_key", ""))

        batch = self.processor.process_queries([payload["query"]])
        batch = {k: v.to(self.model.device) for k, v in batch.items()}
        with torch.no_grad():
            self.model.rope_deltas = None
            embeddings = self.model(**batch)
        return {"vectors": embeddings[0].detach().cpu().float().numpy().tolist()}