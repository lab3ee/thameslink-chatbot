import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from loguru import logger

from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import TextNode
from app.core.config import settings

class IngestionService:
    """
    Parses train maintenance manuals (PDF / Markdown / Text), preserves table formatting,
    generates hierarchical chunks, and enriches nodes with railway fleet metadata.
    """

    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        self.node_parser = SentenceSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def load_document(self, file_path: Path) -> List[Document]:
        """
        Parses document using Docling if available, falling back to clean text/markdown reader.
        """
        ext = file_path.suffix.lower()
        docs = []

        if ext == ".pdf":
            try:
                from llama_index.readers.docling import DoclingReader
                logger.info(f"Parsing PDF with DoclingReader: {file_path}")
                reader = DoclingReader()
                docs = reader.load_data(file_path=str(file_path))
            except ImportError:
                logger.warning("DoclingReader not installed; using standard PyPDF/text fallback.")
                import pypdf
                reader = pypdf.PdfReader(str(file_path))
                for page_idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        docs.append(Document(
                            text=text,
                            metadata={"page_number": page_idx + 1, "file_path": str(file_path)}
                        ))
        elif ext in [".md", ".txt"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
                docs.append(Document(
                    text=text,
                    metadata={"file_path": str(file_path), "page_number": 1}
                ))
        else:
            raise ValueError(f"Unsupported manual format: {ext}")

        return docs

    def process_and_chunk(
        self,
        docs: List[Document],
        train_type: str,
        subsystem: str,
        manual_name: str,
        document_category: str = "fleet_manual"
    ) -> List[TextNode]:
        """
        Splits documents into sized chunks and enriches each node with domain metadata.
        document_category: 'fleet_manual' | 'general_reference'
        """
        nodes = self.node_parser.get_nodes_from_documents(docs)
        
        for node in nodes:
            # Preserve existing page numbers if extracted by reader
            page = node.metadata.get("page_number", 1)
            
            # Enrich with domain metadata for pre-filtering
            node.metadata["train_type"] = train_type.strip() if train_type else "General"
            node.metadata["subsystem"] = subsystem.strip() if subsystem else "General"
            node.metadata["manual_name"] = manual_name.strip()
            node.metadata["page_number"] = page
            node.metadata["document_category"] = document_category

            # Try to identify section titles from first lines if markdown headings exist
            first_line = node.get_content().split("\n")[0]
            if first_line.startswith("#"):
                node.metadata["section_title"] = first_line.lstrip("#").strip()
            elif "section_title" not in node.metadata:
                node.metadata["section_title"] = f"Manual Reference (Page {page})"

        logger.info(
            f"Created {len(nodes)} chunks for '{manual_name}' "
            f"[{train_type or 'General'} / {subsystem or 'General'}] "
            f"category={document_category}"
        )
        return nodes
