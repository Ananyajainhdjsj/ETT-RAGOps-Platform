"""
Configuration management for RAGOps Platform.
Centralizes all settings and validates environment variables.
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings with validation."""
    
    def __init__(self):
        # API Settings
        self.api_title = "RAGOps Platform"
        self.api_version = "1.0.0"
        self.api_description = "Retrieval-Augmented Generation Platform"
        
        # LLM Settings
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        # Embedding Settings
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # Database Settings
        self.db_path = os.getenv("DB_PATH", "rag_store.sqlite")
        
        # Document Processing Settings
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "300"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "50"))
        
        # Retrieval Settings
        self.default_top_k = int(os.getenv("DEFAULT_TOP_K", "5"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
        
        # File Upload Settings
        self.max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
        self.allowed_extensions = [".pdf"]
        self.upload_dir = os.getenv("UPLOAD_DIR", "uploads")
        
        self._validate()
    
    def _validate(self):
        """Validate critical configuration."""
        if not self.gemini_api_key:
            print("WARNING: GEMINI_API_KEY not set. LLM features will fail.")
        
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError(f"chunk_overlap ({self.chunk_overlap}) must be < chunk_size ({self.chunk_size})")
        
        if not (50 <= self.chunk_size <= 1000):
            raise ValueError(f"chunk_size must be 50-1000, got {self.chunk_size}")


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


settings = get_settings()