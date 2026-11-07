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
        Parses document extracting page-by-page text so that chunk metadata
        accurately reflects the real document page numbers.
        Uses pypdfium2 (high performance, accurate page boundaries) for PDFs.
        """
        ext = file_path.suffix.lower()
        docs = []

        if ext == ".pdf":
            try:
                import pypdfium2 as pdfium
                logger.info(f"Extracting pages from PDF with pypdfium2: {file_path.name}")
                pdf = pdfium.PdfDocument(str(file_path))
                total_pages = len(pdf)
                logger.info(f"PDF {file_path.name} has {total_pages} pages")

                for page_idx in range(total_pages):
                    page = pdf[page_idx]
                    text_page = page.get_textpage()
                    text = text_page.get_text_range() or ""
                    
                    if text.strip():
                        docs.append(Document(
                            text=text,
                            metadata={
                                "page_number": page_idx + 1,
                                "file_path": str(file_path),
                                "total_pages": total_pages
                            }
                        ))
                logger.info(f"Loaded {len(docs)} non-empty pages from {file_path.name}")
            except Exception as e:
                logger.error(f"Error reading PDF with pypdfium2: {e}")
                raise
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
        document_category: str = "fleet_manual",
        source_file_name: Optional[str] = None
    ) -> List[TextNode]:
        """
        Splits documents into sized chunks and enriches each node with domain metadata.
        Guarantees that every chunk gets tagged with:
          - manual_name: custom title or file name
          - source_file: actual physical file name (e.g. etcs_broschuere_ES64U2.pdf)
          - page_number: exact page from pypdfium2 (1, 2, 3...)
          - document_category: fleet_manual | general_reference
        """
        nodes = self.node_parser.get_nodes_from_documents(docs)
        
        for node in nodes:
            # Preserve the exact page number from the parent page document
            page = node.metadata.get("page_number", 1)
            file_path = node.metadata.get("file_path", "")
            file_name = source_file_name or (Path(file_path).name if file_path else "Unknown File")
            resolved_manual_name = manual_name.strip() if manual_name else file_name

            # Attach robust metadata directly to the chunk payload
            node.metadata["manual_name"] = resolved_manual_name
            node.metadata["source_file"] = file_name
            node.metadata["page_number"] = int(page)
            node.metadata["train_type"] = train_type.strip() if train_type else "General"
            node.metadata["subsystem"] = subsystem.strip() if subsystem else "General"
            node.metadata["document_category"] = document_category

            # Identify section title if marked by a markdown heading
            first_line = node.get_content().split("\n")[0]
            if first_line.startswith("#"):
                node.metadata["section_title"] = first_line.lstrip("#").strip()
            elif "section_title" not in node.metadata:
                node.metadata["section_title"] = f"Page {page}"

        logger.info(
            f"Created {len(nodes)} chunks for '{resolved_manual_name}' (file: {file_name}) "
            f"[{train_type or 'General'} / {subsystem or 'General'}] "
            f"category={document_category}"
        )
        return nodes
