import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from google import genai
from openai import OpenAI

load_dotenv()

class LLMProvider(ABC):
    """Interface for an LLM Provider"""

    @abstractmethod
    def generate(self,prompt:str)->str:
        """Generate a response from the provider."""
        raise NotImplementedError

class GeminiProvider(LLMProvider):
    """LLM Provider using Google Gemini."""

    def __init__(self,model:str="gemini-3.6-flash"):
        api_key=os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured") 
        self.client=genai.Client(api_key=api_key)
        self.model=model

    def generate(self,prompt:str)->str:
        response=self.client.models.generate_content(
            model=self.model,
            contents=prompt
        ) 
        if not response.text:
            raise ValueError("Gemini returned an empty response.")
        return response.text

class OpenRouterProvider(LLMProvider):
    """LLM provider using OpenRouter's OpenAI-compatible API."""
    def __init__(self,model:str="google/gemini-2.5-flash"):
        api_key=os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is not configured.")
        self.client=OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model=model

    def generate(self,prompt:str)->str:
        response = self.client.chat.completions.create(
        model=self.model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=2048)
        content=response.choices[0].message.content
        if not content:
            raise ValueError("OpenRouter returned an empty response.")
        return content      