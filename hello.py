from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic()

response = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=200,
    messages=[
        {"role": "user", "content": "Say hello in French"}
    ],
)

print(response.content[0].text)