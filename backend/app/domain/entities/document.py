from dataclasses import dataclass
from enum import Enum
from typing import Optional


class DocumentType(Enum):
    TEXT = "text"
    PDF = "pdf"
    VIDEO = "video"
    IMAGE = "image"
    JSON = "json"
    AUDIO = "audio"


@dataclass
class Document:
    """
    Representa um documento a ser indexado.
    """
    id: str
    content: str
    doc_type: DocumentType
    metadata: Optional[dict] = None
    embedding: Optional[list[float]] = None

    @property
    def is_indexed(self) -> bool:
        """Verifica se o documento já possui embedding."""
        return self.embedding is not None 