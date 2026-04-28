from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessageChunk,AIMessage
class ChatOpenAIWithReasoning(ChatOpenAI):
    """Preserve provider-native reasoning keys on streamed chunks."""

    def _convert_chunk_to_generation_chunk(self, chunk: dict, default_chunk_class: type, base_generation_info: dict | None):
        generation_chunk = super()._convert_chunk_to_generation_chunk(
            chunk, default_chunk_class, base_generation_info
        )
        if generation_chunk is None:
            return None

        try:
            choices = chunk.get("choices", []) or chunk.get("chunk", {}).get("choices", [])
            if not choices:
                return generation_chunk
            delta = choices[0].get("delta") or {}
            if not isinstance(delta, dict):
                return generation_chunk

            reasoning_tok = delta.get("reasoning") or delta.get("reasoning_content")
            if reasoning_tok and isinstance(generation_chunk.message, AIMessageChunk):
                generation_chunk.message.additional_kwargs["reasoning"] = reasoning_tok
                generation_chunk.message.additional_kwargs["reasoning_content"] = reasoning_tok
        except Exception:
            # Never break streaming because of metadata extraction.
            pass

        return generation_chunk



def _extract_reasoning(msg: AIMessage) -> str:
    out = ""
    additional = getattr(msg, "additional_kwargs", None)
    if isinstance(additional, dict):
        val = additional.get("reasoning") or additional.get("reasoning_content")
        if isinstance(val, str):
            out += val
    blocks = getattr(msg, "content_blocks", None)
    if isinstance(blocks, list):
        for block in blocks:
            if isinstance(block, dict) and block.get("type") == "reasoning":
                val = block.get("reasoning") or block.get("text")
                if isinstance(val, str):
                    out += val
    return out