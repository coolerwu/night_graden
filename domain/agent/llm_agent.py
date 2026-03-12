"""LLM Agent for Night Garden - Core domain logic only"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMAgent(ABC):
    """Abstract base class for LLM agents"""
    
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
    
    @abstractmethod
    def invoke(self, prompt: str) -> str:
        """Invoke LLM with given prompt and return response"""
        pass
    
    @abstractmethod
    def invoke_with_json_output(self, prompt: str) -> Dict[str, Any]:
        """Invoke LLM with given prompt and return structured JSON response"""
        pass


class SimpleLLMAgent(LLMAgent):
    """Simple implementation of LLM agent using environment configuration"""
    
    def __init__(self, model_name: str = "gpt-4o", provider: str = "openai"):
        super().__init__(model_name)
        self.provider = provider
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize LLM client based on provider"""
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        if self.provider == "openai":
            from openai import OpenAI
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            self.client = OpenAI(api_key=api_key)
        elif self.provider == "anthropic":
            from anthropic import Anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def invoke(self, prompt: str) -> str:
        """Invoke LLM with given prompt and return response"""
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            return response.content[0].text
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def invoke_with_json_output(self, prompt: str) -> Dict[str, Any]:
        """Invoke LLM with given prompt and return structured JSON response"""
        import json
        
        # Add instruction to return JSON
        json_prompt = f"{prompt}\n\nPlease return your response as a valid JSON object."
        
        response = self.invoke(json_prompt)
        
        try:
            # Try to extract JSON from response
            # Handle cases where LLM wraps JSON in markdown code blocks
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_str = response[start:end] if end != -1 else response[start:]
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_str = response[start:end] if end != -1 else response[start:]
            else:
                json_str = response
            
            return json.loads(json_str.strip())
        except (json.JSONDecodeError, ValueError) as e:
            # If JSON parsing fails, return error structure
            return {
                "error": "Failed to parse JSON response",
                "raw_response": response,
                "exception": str(e)
            }