import re
from typing import List, Dict, Any, Optional
from loguru import logger
from llama_index.core.schema import NodeWithScore

class PromptBuilder:
    """
    Constructs strict grounding prompts for train technicians troubleshooting fault codes.
    Prevents hallucinations and enforces mandatory manual citations.
    """

    SYSTEM_PROMPT = """You are a technical reference assistant for railway maintenance and operations staff. You have access to official maintenance manuals, rulebooks, technical specifications, and safety documents.

ABSOLUTE RULES — these override everything else:
1. You MUST NOT use any knowledge from your training data. You have no independent railway knowledge.
2. You MUST NOT invent, infer, or extrapolate any procedure, specification, measurement, rule, or component designation that is not explicitly stated in the provided manual excerpts.
3. If the manual excerpts do not contain information relevant to the question, you MUST respond with exactly this sentence and nothing else:
   "The provided manuals do not contain information relevant to this query."
4. If the excerpts partially cover the question, state only what the manuals explicitly say and clearly indicate which parts are not covered.
5. Never use phrases like "typically", "generally", "in most cases", "you should", or "it is common to" — these indicate inference from training data, which is forbidden.

OUTPUT FORMAT:
Use clean, professional technical Markdown. Do NOT use emojis.
Structure your response appropriately for the type of question:

- For fault code queries: use sections Fault Diagnosis, Safety & Isolation Precautions, Remedial Action Procedure, Component & Circuit Breaker Designations.
- For procedural questions: use numbered steps.
- For explanatory or descriptive questions: use clear paragraphs with bold sub-headings where helpful.
- For regulatory or rules questions: quote the relevant rule or clause directly, then explain its application.

Always end your response with a Manual Reference section listing the manual name, section, and page number the information was drawn from."""

    @classmethod
    def format_context_prompt(cls, query: str, nodes: List[NodeWithScore], train_type: Optional[str] = None, subsystem: Optional[str] = None) -> str:
        context_parts = []
        for i, node in enumerate(nodes, start=1):
            metadata = node.metadata or {}
            manual = metadata.get("manual_name", "Unknown Manual")
            section = metadata.get("section_title", "Unknown Section")
            page = metadata.get("page_number", "N/A")
            train = metadata.get("train_type", train_type or "Generic")
            subsys = metadata.get("subsystem", subsystem or "General")
            
            header = f"[Manual: {manual} | Section: {section} | Page: {page}]"
            content = node.get_content().strip()
            context_parts.append(f"{header}\n{content}")

        joined_context = "\n\n".join(context_parts) if context_parts else "No relevant manual excerpts found."

        meta_info = []
        if train_type:
            meta_info.append(f"Train Class: {train_type}")
        if subsystem:
            meta_info.append(f"Subsystem: {subsystem}")
        meta_str = f" ({', '.join(meta_info)})" if meta_info else ""

        user_prompt = f"""{cls.SYSTEM_PROMPT}

### TECHNICIAN QUERY{meta_str}:
{query}

### OFFICIAL REFERENCE MANUAL CONTEXT:
{joined_context}

### OUTPUT FORMAT REQUIREMENTS:
Format your reply clearly in clean, professional technical Markdown for depot technicians. Do NOT use emojis.
- Use clean bold section headers:
  ### Fault Diagnosis
  ### Safety & Isolation Precautions
  ### Remedial Action Procedure
  ### Component & Circuit Breaker Designations
- Use ordered numbers (1., 2., 3.) for the remedial action procedure.
- Put all component codes, switches, and circuit breakers in backticks (e.g. `=24-F01`, `=24-S02`).
- Never dump raw unformatted text blocks.
- Answer strictly from the excerpts provided."""

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
