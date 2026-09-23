from app.ai.providers import OpenRouterProvider

provider = OpenRouterProvider()

response = provider.generate(
    "Return exactly the word HELLO."
)

print(response)