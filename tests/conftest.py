class MemoryConversationManager:
    def __init__(self):
        self.messages = []

    def add_message(self, conversation_id, role, content, metadata=None):
        self.messages.append(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "metadata": metadata,
            }
        )
        return len(self.messages)

    def get_context(self, conversation_id):
        return self.messages


class SequenceLLM:
    def __init__(self, *outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def chat(self, prompt, system_prompt=None, **kwargs):
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        return next(self.outputs)
