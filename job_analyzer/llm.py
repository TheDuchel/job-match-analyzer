from dotenv import load_dotenv
from anthropic import Anthropic
from os import getenv

class LLMClient:
    def __init__(self):
        load_dotenv()
        self.client = Anthropic()
        self.llm_model = getenv("LLM_MODEL", "claude-sonnet-5-5")

    def complete(self, prompt: str, max_tokens: int = 200) ->str:
        response = self.client.messages.create(
            model=self.llm_model,
            max_tokens=max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        text_parts = [block.text for block in response.content if block.type == "text"]
        return "".join(text_parts)

if __name__ == "__main__":
    llm = LLMClient()
    print(llm.complete("Say hello in French"))