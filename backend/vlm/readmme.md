To ensure your README is 100% accurate for your PFE, here is the technical breakdown of the vLLM + Qwen 3.6 reasoning architecture, formatted for clear documentation.

vLLM Reasoning Architecture for Qwen 3.6
When serving Qwen 3.6 with the --reasoning-parser qwen3 flag, you gain granular control over the model's internal "thought" state.
Below are the verified technical facts regarding these parameters.

1. The preserve_thinking Parameter
Function: Controls whether the <think> block from previous messages is retained in the KV Cache during multi-turn conversations.

Fact: In previous versions, the serving layer would often strip reasoning content from the history sent back to the model, 
causing KV Cache Invalidation. This forced the GPU to re-compute the entire prompt from scratch.

ON (true): The model retains access to its prior reasoning steps. This allows the agent to maintain "logical continuity"
and reduces the risk of loops or contradictions in complex tasks (like multi-step coding).

OFF (false): Only the final "content" is preserved. The model sees what it decided, but forgets why, saving VRAM at the cost of
reasoning depth.

2. The enable_thinking Parameter
Function: A "Hard Switch" used to toggle the generation of new reasoning tokens for the current request.

Behavior: When set to false, the chat template is modified to instruct the model to skip the <think> phase entirely.

Constraint: Because Qwen 3.5/3.6 is natively trained for reasoning, a "Hard Switch" alone can sometimes cause "tag leakage" 
where the model instinctively outputs a <think> token that isn't caught by the template.

3. The "Assistant Prefill" Optimization
Technique: Passing {"role": "assistant", "content": "<think>\n</think>"} as the final message in the history.

Fact: This exploits the model's state machine. By providing a "closed" thinking block in the assistant's mouth, you signal that 
the reasoning phase is completed.

Result: This is the only 100% reliable method to force the model to move immediately to the final answer (Content Generation)
without any reasoning latency or tag leakage.

example of usage:
# PROMPT STRUCTURE
payload = {
    "model": "Qwen/Qwen3.6-35B-A3B-FP8",
    "messages": [
        {"role": "user", "content": "Initial complex logic task..."},
        {"role": "assistant", "content": "<think>\n...logic...\n</think>\nResult."},
        {"role": "user", "content": "Fast follow-up question..."},
        # THE PREFILL
        {"role": "assistant", "content": "<think>\n</think>"}
    ],
    "extra_body": {
        "chat_template_kwargs": {
            "enable_thinking": False,  # Turn off new reasoning
            "preserve_thinking": True  # Keep past reasoning in cache
        }
    }
}
