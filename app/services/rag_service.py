from typing import List, Optional, Tuple
from loguru import logger

from llama_index.core import VectorStoreIndex, StorageContext, Settings as LlamaSettings
from llama_index.core.vector_stores.types import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
    FilterCondition,
    VectorStoreQueryMode
)
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.llms import ChatMessage, MessageRole
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
import qdrant_client

from app.core.config import settings
from app.services.prompt_builder import PromptBuilder
from app.schemas.query import CitationSource, QueryResponse

NOT_FOUND_ANSWER = (
    "The provided maintenance manuals do not contain troubleshooting information "
    "for this fault code or query. Please consult your depot technical support team "
    "or raise a request with Rolling Stock Engineering."
)

class RAGService:
    """
    Manages hybrid search (dense embeddings + BM25 keyword matching) in Qdrant,
    metadata pre-filtering by train_type/subsystem, and grounded LLM generation via Ollama.
    """

    def __init__(self):
        logger.info(f"Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        self.client = qdrant_client.QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        
        # Configure LlamaIndex global models using local Ollama
        self.llm = Ollama(
            model=settings.LLM_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            request_timeout=settings.LLM_REQUEST_TIMEOUT
        )
        self.embed_model = OllamaEmbedding(
            model_name=settings.EMBED_MODEL,
            base_url=settings.OLLAMA_BASE_URL
        )

        LlamaSettings.llm = self.llm
        LlamaSettings.embed_model = self.embed_model

        # Setup Qdrant vector store with hybrid search enabled
        self.vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=settings.QDRANT_COLLECTION,
            enable_hybrid=True,
            fastembed_sparse_model="Qdrant/bm25"
        )
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

    def is_file_already_ingested(self, file_name: str) -> bool:
        """
        Checks Qdrant to see if chunks for this file already exist in the collection.
        Prevents redundant re-embedding when adding new manuals.
        """
        try:
            from qdrant_client.http import models as qmodels
            res = self.client.scroll(
                collection_name=settings.QDRANT_COLLECTION,
                scroll_filter=qmodels.Filter(
                    should=[
                        qmodels.FieldCondition(
                            key="source_file",
                            match=qmodels.MatchValue(value=file_name)
                        ),
                        qmodels.FieldCondition(
                            key="manual_name",
                            match=qmodels.MatchValue(value=file_name)
                        )
                    ]
                ),
                limit=1,
                with_payload=False,
                with_vectors=False
            )
            points, _ = res
            return len(points) > 0
        except Exception:
            # If collection does not exist yet, obviously not ingested
            return False

    def upsert_nodes(self, nodes: List[TextNode]) -> int:
        """
        Embeds nodes in batches using get_text_embedding_batch(), then upserts to Qdrant.
        Batching is significantly faster than one-at-a-time embedding for large documents
        because Ollama can pipeline multiple inputs in a single call.
        """
        if not nodes:
            return 0

        total = len(nodes)
        batch_size = settings.EMBED_BATCH_SIZE
        num_batches = (total + batch_size - 1) // batch_size

        logger.info(
            f"Embedding {total} chunks in {num_batches} batches of {batch_size} "
            f"-> collection '{settings.QDRANT_COLLECTION}'"
        )

        for batch_idx in range(num_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, total)
            batch = nodes[start:end]

            # Identify which nodes in this batch still need an embedding
            texts_to_embed = [
                (i, node) for i, node in enumerate(batch) if node.embedding is None
            ]

            if texts_to_embed:
                idxs, pending_nodes = zip(*texts_to_embed)
                embeddings = self.embed_model.get_text_embedding_batch(
                    [n.get_content() for n in pending_nodes],
                    show_progress=False
                )
                for node, embedding in zip(pending_nodes, embeddings):
                    node.embedding = embedding

            self.vector_store.add(batch)
            logger.info(f"  Batch {batch_idx + 1}/{num_batches} upserted ({end}/{total} chunks done)")

        logger.info(f"Ingestion complete: {total} chunks indexed.")
        return total

    def _filter_by_relevance(self, nodes: List[NodeWithScore]) -> List[NodeWithScore]:
        """
        Discard chunks whose retrieval score falls below the minimum relevance threshold.
        This is the primary hallucination guard: if no chunk is sufficiently relevant,
        the LLM never receives context and therefore cannot invent an answer.
        """
        if not nodes:
            return []
        qualified = [n for n in nodes if n.score is not None and n.score >= settings.MIN_RELEVANCE_SCORE]
        discarded = len(nodes) - len(qualified)
        if discarded:
            logger.warning(
                f"Discarded {discarded}/{len(nodes)} chunks below relevance threshold "
                f"({settings.MIN_RELEVANCE_SCORE}). Scores: {[round(n.score, 3) for n in nodes]}"
            )
        return qualified

    def query(
        self,
        query_text: str,
        train_type: Optional[str] = None,
        subsystem: Optional[str] = None,
        top_k: int = 5
    ) -> QueryResponse:
        """
        Executes hybrid retrieval with metadata filtering and returns grounded response with citations.
        """
        # Build a compound filter:
        # Match chunks that are EITHER:
        #   (a) tagged with the requested train_type AND subsystem (fleet manuals), OR
        #   (b) tagged as document_category == "general_reference" (rulebooks, standards, policy docs)
        # This ensures general reference documents are always searched alongside fleet-specific results.
        general_filter = MetadataFilter(
            key="document_category",
            value="general_reference",
            operator=FilterOperator.EQ
        )

        fleet_conditions = []
        if train_type and train_type.strip():
            fleet_conditions.append(
                MetadataFilter(key="train_type", value=train_type.strip(), operator=FilterOperator.EQ)
            )
        if subsystem and subsystem.strip():
            fleet_conditions.append(
                MetadataFilter(key="subsystem", value=subsystem.strip(), operator=FilterOperator.EQ)
            )

        if fleet_conditions:
            # AND between train_type/subsystem filters, then OR that block with general_reference
            fleet_block = MetadataFilters(filters=fleet_conditions, condition=FilterCondition.AND)
            metadata_filters = MetadataFilters(
                filters=[fleet_block, general_filter],
                condition=FilterCondition.OR
            )
        else:
            # No fleet filters provided — search all documents (general + all fleet manuals)
            metadata_filters = None

        detected_codes = PromptBuilder.extract_fault_codes(query_text)
        detected_code_str = ", ".join(detected_codes) if detected_codes else None

        # Build index instance from existing vector store
        index = VectorStoreIndex.from_vector_store(
            vector_store=self.vector_store,
            storage_context=self.storage_context
        )

        # Configure retriever for hybrid mode (sparse BM25 + dense bge-m3)
        retriever = index.as_retriever(
            vector_store_query_mode=VectorStoreQueryMode.HYBRID,
            similarity_top_k=top_k,
            sparse_top_k=top_k,
            alpha=settings.HYBRID_ALPHA,
            filters=metadata_filters
        )

        retrieved_nodes = retriever.retrieve(query_text)
        logger.info(
            f"Retrieved {len(retrieved_nodes)} raw nodes. "
            f"Scores: {[round(n.score, 3) for n in retrieved_nodes if n.score is not None]}"
        )

        # --- GROUNDING GATE ---
        # Discard low-relevance chunks before they ever reach the LLM.
        # If nothing passes the threshold, return the standard "not found" response immediately.
        relevant_nodes = self._filter_by_relevance(retrieved_nodes)

        if not relevant_nodes:
            logger.info("No chunks passed relevance threshold — returning not-found response without calling LLM.")
            return QueryResponse(
                answer=NOT_FOUND_ANSWER,
                found_in_manuals=False,
                citations=[],
                fault_code_detected=detected_code_str
            )

        # Build citations only from qualified nodes
        citations: List[CitationSource] = []
        for n in relevant_nodes:
            meta = n.metadata or {}
            citations.append(CitationSource(
                manual_name=meta.get("manual_name", "Maintenance Manual"),
                section=meta.get("section_title"),
                page=meta.get("page_number"),
                text_snippet=n.get_content()[:280] + "...",
                score=n.score
            ))

        # Build user-facing context prompt from relevant chunks only
        user_prompt = PromptBuilder.format_context_prompt(
            query=query_text,
            nodes=relevant_nodes,
            train_type=train_type,
            subsystem=subsystem
        )

        # --- STRICT CHAT MESSAGES ---
        # Use the chat() API so the system role is enforced as a hard constraint,
        # not just advisory text. This is the key fix for instruction-following on small models.
        messages = [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=PromptBuilder.SYSTEM_PROMPT
            ),
            ChatMessage(
                role=MessageRole.USER,
                content=user_prompt
            ),
        ]

        response = self.llm.chat(messages)
        answer_text = response.message.content.strip()

        # Sanitize output: Strip any prompt artifacts that a small LLM may mirror
        unwanted_headers = [
            "## TECHNICIAN QUERY:",
            "### TECHNICIAN QUERY:",
            "### OUTPUT FORMAT REQUIREMENTS:",
            "OUTPUT FORMAT REQUIREMENTS:",
            "Provide only the direct technical answer below:",
            "Reference Manual Excerpts:"
        ]
        for header in unwanted_headers:
            if header in answer_text:
                answer_text = answer_text.replace(header, "")

        # Strip duplicate "### MANUAL REFERENCE:" blocks generated by the LLM (n8n adds these automatically)
        if "### MANUAL REFERENCE" in answer_text:
            parts = answer_text.split("### MANUAL REFERENCE")
            answer_text = parts[0] + parts[1].split("\n\n", 1)[-1] if len(parts) > 1 else parts[0]

        answer_text = answer_text.strip()

        return QueryResponse(
            answer=answer_text,
            found_in_manuals=True,
            citations=citations,
            fault_code_detected=detected_code_str
        )
