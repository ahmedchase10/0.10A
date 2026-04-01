import requests
import base64
from io import BytesIO
import os

from dotenv import load_dotenv

load_dotenv()

ENCODE_DOCS_URL = os.getenv("ENCODE_DOCS_URL")
ENCODE_QUERY_URL = os.getenv("ENCODE_QUERY_URL")
API_KEY = os.getenv("API_KEY")


def process_docs_remote(images: list) -> list:
    b64_images = []
    for img in images:
        buf = BytesIO()
        img.save(buf, format="PNG")
        b64_images.append(base64.b64encode(buf.getvalue()).decode())

    response = requests.post(
        ENCODE_DOCS_URL,
        json={"api_key": API_KEY, "images": b64_images}
    )
    response.raise_for_status()
    return response.json()["vectors"]


def process_query_remote(query: str) -> list:
    response = requests.post(
        ENCODE_QUERY_URL,
        json={"api_key": API_KEY, "query": query}
    )
    response.raise_for_status()
    return response.json()["vectors"]