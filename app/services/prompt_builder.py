import re
from typing import List, Dict, Any, Optional
from loguru import logger
from llama_index.core.schema import NodeWithScore

class PromptBuilder:
    """
    Constructs strict grounding prompts for train technicians troubleshooting fault codes.
    Prevents hallucinations and enforces mandatory manual citations.
    """

    SYSTEM_PROMPT = """You are a technical reference assistant for railway maintenance and operations staff.
You have access to excerpts from official maintenance manuals, rulebooks, technical specifications, and safety documents.

ABSOLUTE RULES:
1. Use ONLY the facts directly stated in the Reference Manual Excerpts. You have no independent railway knowledge.
2. If the excerpts do not contain enough information to answer the question, output ONLY:
   "The provided manuals do not contain information relevant to this query."
3. Do NOT repeat or echo the user's question, prompt instructions, system rules, or headers like "TECHNICIAN QUERY:" or "OUTPUT FORMAT REQUIREMENTS:".
4. Do NOT output a citations section in your text (citations are automatically attached by the system).
5. Output ONLY the direct technical answer in clean Markdown, without emojis.
6. If the excerpts are in German and the question is in English (or vice versa), translate the technical information accurately."""

    @classmethod
    def format_context_prompt(cls, query: str, nodes: List[NodeWithScore], train_type: Optional[str] = None, subsystem: Optional[str] = None) -> str:
        context_parts = []
        for i, node in enumerate(nodes, start=1):
            metadata = node.metadata or {}
            manual = metadata.get("manual_name", "Unknown Manual")
            section = metadata.get("section_title", "Unknown Section")
            page = metadata.get("page_number", "N/A")
            
            header = f"--- [Excerpt {i} | Manual: {manual} | Section: {section} | Page: {page}] ---"
            content = node.get_content().strip()
            context_parts.append(f"{header}\n{content}")

        joined_context = "\n\n".join(context_parts) if context_parts else "No excerpts available."

        meta_info = []
        if train_type and train_type.strip() and train_type.lower() != "general":
            meta_info.append(f"Train Class: {train_type.strip()}")
        if subsystem and subsystem.strip() and subsystem.lower() != "general":
            meta_info.append(f"Subsystem: {subsystem.strip()}")
        meta_str = f" Context: ({', '.join(meta_info)})\n" if meta_info else ""

        user_prompt = f"""Reference Manual Excerpts:
{joined_context}

{meta_str}Question: {query}

Provide only the direct technical answer below:"""

        return user_prompt

    @classmethod
    def extract_fault_codes(cls, text: str) -> List[str]:
        """
        Regex patterns matching common railway fault code naming schemes
        e.g., FC 4103, FC_721, E2041, ERR-102, DG-04, 700-TCMS-12
        """
        patterns = [
            r'\b(?:FC|ERR|FAULT|CODE)[\s_-]?[A-Z0-9]{2,6}\b',
            r'\b[A-Z]{1,3}-\d{2,5}\b',
            r'\bE\d{3,5}\b'
        ]
        codes = []
        for pat in patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            codes.extend([m.upper() for m in matches])
        return list(dict.fromkeys(codes))
