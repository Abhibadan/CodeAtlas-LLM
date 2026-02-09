"""
AI Model Adapter Module

This module provides a unified interface for different AI providers (Gemini, OpenAI, Ollama).
It uses the adapter pattern to abstract away provider-specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Any
from config import ai_config, google_config, openai_config, ollama_config
import os


class AIModelAdapter(ABC):
    """Abstract base class for AI model adapters"""
    
    @abstractmethod
    def get_embeddings(self):
        """Return the embeddings model for the provider"""
        pass
    
    @abstractmethod
    def get_chat_model(self):
        """Return the chat model for the provider"""
        pass


class GeminiAdapter(AIModelAdapter):
    """Adapter for Google Gemini AI models"""
    
    def __init__(self):
        """
        Initialize Gemini adapter
        """
        self.api_key = google_config["api_key"]
        self.embedding_model_name = google_config["embedding_model"]
        self.chat_model_name = google_config["chat_model"]
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
    
    def get_embeddings(self):
        """Return Google Generative AI embeddings"""
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        
        return GoogleGenerativeAIEmbeddings(
            model=self.embedding_model_name,
            google_api_key=self.api_key
        )
    
    def get_chat_model(self):
        """Return Google Generative AI chat model"""
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        return ChatGoogleGenerativeAI(
            model=self.chat_model_name,
            google_api_key=self.api_key
        )


class OpenAIAdapter(AIModelAdapter):
    """Adapter for OpenAI models"""
    
    def __init__(self):
        """
        Initialize OpenAI adapter
        """
        self.api_key = openai_config["api_key"]
        self.embedding_model_name = openai_config["embedding_model"]
        self.chat_model_name = openai_config["chat_model"]
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    def get_embeddings(self):
        """Return OpenAI embeddings"""
        from langchain_openai import OpenAIEmbeddings
        
        return OpenAIEmbeddings(
            model=self.embedding_model_name,
            openai_api_key=self.api_key
        )
    
    def get_chat_model(self):
        """Return OpenAI chat model"""
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=self.chat_model_name,
            openai_api_key=self.api_key
        )


class OllamaAdapter(AIModelAdapter):
    """Adapter for Ollama models (local/self-hosted)"""
    
    def __init__(self):
        """
        Initialize Ollama adapter
        """
        self.base_url = ollama_config["base_url"]
        self.embedding_model_name = ollama_config["embedding_model"]
        self.chat_model_name = ollama_config["chat_model"]
    
    def get_embeddings(self):
        """Return Ollama embeddings"""
        from langchain_community.embeddings import OllamaEmbeddings
        
        return OllamaEmbeddings(
            model=self.embedding_model_name,
            base_url=self.base_url
        )
    
    def get_chat_model(self):
        """Return Ollama chat model"""
        from langchain_community.chat_models import ChatOllama
        
        return ChatOllama(
            model=self.chat_model_name,
            base_url=self.base_url
        )


class AIModelFactory:
    """Factory class to create AI model adapters based on configuration"""
    
    # Map provider names to adapter classes
    _adapters = {
        "gemini": GeminiAdapter,
        "openai": OpenAIAdapter,
        "ollama": OllamaAdapter,
    }
    
    @classmethod
    def create_adapter() -> AIModelAdapter:
        """
        Create an AI model adapter based on the provider
        
        Args:
            provider: Name of the AI provider (gemini, openai, ollama)
            config: Configuration dictionary for the provider
            
        Returns:
            AIModelAdapter instance
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = ai_config.get("provider", "gemini").lower()
        
        if provider not in cls._adapters:
            supported = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Unsupported AI provider: {provider}. "
                f"Supported providers: {supported}"
            )
        
        adapter_class = cls._adapters[provider]
        return adapter_class()
    
    @classmethod
    def get_supported_providers(cls):
        """Return list of supported providers"""
        return list(cls._adapters.keys())
