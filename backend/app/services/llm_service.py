from groq import Groq
from app.config import GROQ_API_KEY, LLM_MODEL

class LLMService:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)

    def get_response(self, prompt, system_prompt="You are a helpful assistant."):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            model=LLM_MODEL,
        )
        return chat_completion.choices[0].message.content

llm_service = LLMService()