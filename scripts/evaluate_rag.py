"""
scripts/evaluate_rag.py
Empirical Evaluation Harness for Block 5 (Evidence)
HTW Berlin - Emerging AI Showcase Examination
Evaluates Retrieval Recall, Citation Accuracy, Grounding Gate Precision,
Negative Rejection, and Generation Grounding.
"""

import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.services.rag_service import RAGService
from app.services.prompt_builder import PromptBuilder

EVAL_CASES = [
    # Category A: Exact Alphanumeric Fault Codes & Component IDs
    {
        "id": "A01",
        "category": "Cat A: Exact Fault Codes",
        "query": "How do I troubleshoot fault code FC 4103 on Class 700?",
        "expected_code": "FC 4103",
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 42,
        "is_negative": False
    },
    {
        "id": "A02",
        "category": "Cat A: Exact Fault Codes",
        "query": "What is the procedure for FC 2814 DC bus overvoltage spike?",
        "expected_code": "FC 2814",
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 58,
        "is_negative": False
    },
    {
        "id": "A03",
        "category": "Cat A: Exact Fault Codes",
        "query": "Remedial actions for FC 1205 exterior door interlock loop open while in motion",
        "expected_code": "FC 1205",
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 84,
        "is_negative": False
    },
    {
        "id": "A04",
        "category": "Cat A: Exact Fault Codes",
        "query": "Which circuit breaker protects the traction converter cooling fan on Class 700?",
        "expected_code": "=24-F01",
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 42,
        "is_negative": False
    },
    {
        "id": "A05",
        "category": "Cat A: Exact Fault Codes",
        "query": "What switch isolates Inverter Unit 1 after repeated FC 4103 faults?",
        "expected_code": "=24-S02",
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 42,
        "is_negative": False
    },
    {
        "id": "A06",
        "category": "Cat A: Exact Fault Codes",
        "query": "What fuse protects the dynamic braking resistor chopper circuit on Class 700?",
        "expected_code": "=22-F14",
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 58,
        "is_negative": False
    },
    {
        "id": "A07",
        "category": "Cat A: Exact Fault Codes",
        "query": "What test pin on the EDCU measures the 24V supply for door proving?",
        "expected_code": "TP-04",
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 84,
        "is_negative": False
    },
    {
        "id": "A08",
        "category": "Cat A: Exact Fault Codes",
        "query": "What switch bypasses the door safety loop under depot supervision?",
        "expected_code": "=41-S10",
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 84,
        "is_negative": False
    },
    {
        "id": "A09",
        "category": "Cat A: Exact Fault Codes",
        "query": "Which microswitch is inspected for mechanical deflection in case of FC 1205?",
        "expected_code": "=41-S08",
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 84,
        "is_negative": False
    },
    {
        "id": "A10",
        "category": "Cat A: Exact Fault Codes",
        "query": "What is the trigger junction temperature threshold for FC 4103?",
        "expected_code": "FC 4103",
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 42,
        "is_negative": False
    },

    # Category B: Technical Specifications & Procedural Inquiries
    {
        "id": "B01",
        "category": "Cat B: Technical Specs & Rules",
        "query": "What is the total weight and axle load of the ES64U2 locomotive with ETCS equipment?",
        "expected_code": None,
        "expected_file": "etcs_broschuere_ES64U2.pdf",
        "expected_page": 5,
        "is_negative": False
    },
    {
        "id": "B02",
        "category": "Cat B: Technical Specs & Rules",
        "query": "What are the traction power supply systems and voltages for the ES 64 U2 locomotive?",
        "expected_code": None,
        "expected_file": "etcs_broschuere_ES64U2.pdf",
        "expected_page": 5,
        "is_negative": False
    },
    {
        "id": "B03",
        "category": "Cat B: Technical Specs & Rules",
        "query": "Who is the manufacturer of the ES64U2 locomotive and what is the wheel arrangement?",
        "expected_code": None,
        "expected_file": "etcs_broschuere_ES64U2.pdf",
        "expected_page": 5,
        "is_negative": False
    },
    {
        "id": "B04",
        "category": "Cat B: Technical Specs & Rules",
        "query": "When was the ES64U2 012 approved for ETCS ON in the ÖBB rail network?",
        "expected_code": None,
        "expected_file": "etcs_broschuere_ES64U2.pdf",
        "expected_page": 5,
        "is_negative": False
    },
    {
        "id": "B05",
        "category": "Cat B: Technical Specs & Rules",
        "query": "What is the maximum rated speed of the ES64U2 locomotive?",
        "expected_code": None,
        "expected_file": "etcs_broschuere_ES64U2.pdf",
        "expected_page": 5,
        "is_negative": False
    },
    {
        "id": "B06",
        "category": "Cat B: Technical Specs & Rules",
        "query": "How does the driver initiate an emergency call using GSM-R radio equipment?",
        "expected_code": None,
        "expected_file": "GSM-R_Handbook_RS523.pdf",
        "expected_page": 1,
        "is_negative": False
    },
    {
        "id": "B07",
        "category": "Cat B: Technical Specs & Rules",
        "query": "What is the registration process on the GSM-R cab radio terminal before train departure?",
        "expected_code": None,
        "expected_file": "GSM-R_Handbook_RS523.pdf",
        "expected_page": 1,
        "is_negative": False
    },
    {
        "id": "B08",
        "category": "Cat B: Technical Specs & Rules",
        "query": "What safety precautions must be observed before entering the 25kV traction cubicle?",
        "expected_code": None,
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 42,
        "is_negative": False
    },
    {
        "id": "B09",
        "category": "Cat B: Technical Specs & Rules",
        "query": "What type of traction motors are used on the Eurosprinter ES64U2?",
        "expected_code": None,
        "expected_file": "etcs_broschuere_ES64U2.pdf",
        "expected_page": 5,
        "is_negative": False
    },
    {
        "id": "B10",
        "category": "Cat B: Technical Specs & Rules",
        "query": "What happens if dynamic braking resistor dynamic contactor fails to pick up on DC line?",
        "expected_code": None,
        "expected_file": "class_700_traction_and_doors_manual.md",
        "expected_page": 58,
        "is_negative": False
    },

    # Category C: Negative Rejection & Out-of-Domain Grounding Tests
    {
        "id": "C01",
        "category": "Cat C: Negative Rejections",
        "query": "What is the troubleshooting procedure for fault code FC 9999?",
        "expected_code": None,
        "expected_file": None,
        "expected_page": None,
        "is_negative": True
    },
    {
        "id": "C02",
        "category": "Cat C: Negative Rejections",
        "query": "How do I reset error code ERR-888 on a Class 800 train?",
        "expected_code": None,
        "expected_file": None,
        "expected_page": None,
        "is_negative": True
    },
    {
        "id": "C03",
        "category": "Cat C: Negative Rejections",
        "query": "What is the pantograph carbon strip replacement torque specification for Class 395?",
        "expected_code": None,
        "expected_file": None,
        "expected_page": None,
        "is_negative": True
    },
    {
        "id": "C04",
        "category": "Cat C: Negative Rejections",
        "query": "What is the recipe for canteen coffee at Hornsey depot?",
        "expected_code": None,
        "expected_file": None,
        "expected_page": None,
        "is_negative": True
    },
    {
        "id": "C05",
        "category": "Cat C: Negative Rejections",
        "query": "What are the diesel engine maintenance intervals for an HST Class 43?",
        "expected_code": None,
        "expected_file": None,
        "expected_page": None,
        "is_negative": True
    },
    {
        "id": "C06",
        "category": "Cat C: Negative Rejections",
        "query": "How do I calibrate the air conditioning thermostat on a Boeing 737?",
        "expected_code": None,
        "expected_file": None,
        "expected_page": None,
        "is_negative": True
    },
    {
        "id": "C07",
        "category": "Cat C: Negative Rejections",
        "query": "Troubleshoot fault code FC 7711 battery ground fault on Class 377",
        "expected_code": None,
        "expected_file": None,
        "expected_page": None,
        "is_negative": True
    },
    {
        "id": "C08",
        "category": "Cat C: Negative Rejections",
        "query": "What is the tire pressure specification for the depot maintenance van?",
        "expected_code": None,
        "expected_file": None,
        "expected_page": None,
        "is_negative": True
    },
    {
        "id": "C09",
        "category": "Cat C: Negative Rejections",
        "query": "What are the Wi-Fi passenger portal configuration settings on Class 700?",
        "expected_code": None,
        "expected_file": None,
        "expected_page": None,
        "is_negative": True
    },
    {
        "id": "C10",
        "category": "Cat C: Negative Rejections",
        "query": "How do I overhaul the bogie secondary suspension on a Shinkansen bullet train?",
        "expected_code": None,
        "expected_file": None,
        "expected_page": None,
        "is_negative": True
    }
]

def run_evaluation_suite():
    print(f"\n=======================================================")
    print(f"HTW Berlin - Emerging AI Showcase: Block 5 (Evidence)")
    print(f"Empirical Evaluation Benchmark (N = {len(EVAL_CASES)} Test Cases)")
    print(f"=======================================================\n")

    rag = RAGService()
    
    from llama_index.core import VectorStoreIndex
    from llama_index.core.vector_stores.types import VectorStoreQueryMode
    
    index = VectorStoreIndex.from_vector_store(
        vector_store=rag.vector_store,
        storage_context=rag.storage_context
    )

    retriever = index.as_retriever(
        vector_store_query_mode=VectorStoreQueryMode.HYBRID,
        similarity_top_k=5,
        sparse_top_k=5,
        alpha=settings.HYBRID_ALPHA
    )

    results = []
    latencies = []
    retrieval_hits_k3 = 0
    retrieval_hits_k5 = 0
    citation_page_matches = 0
    negative_rejection_hits = 0
    false_positive_retrievals = 0

    total_positives = sum(1 for c in EVAL_CASES if not c["is_negative"])
    total_negatives = sum(1 for c in EVAL_CASES if c["is_negative"])

    for i, tc in enumerate(EVAL_CASES, start=1):
        q = tc["query"]
        is_neg = tc["is_negative"]
        
        t0 = time.time()
        retrieved_nodes = retriever.retrieve(q)
        elapsed = time.time() - t0
        latencies.append(elapsed)

        qualified_nodes = rag._filter_by_relevance(retrieved_nodes)
        
        hit_k3 = False
        hit_k5 = False
        page_match = False
        neg_rejected = False
        false_positive = False

        if is_neg:
            # In an out-of-domain case, no chunks should exceed the relevance score floor
            if len(qualified_nodes) == 0:
                neg_rejected = True
                negative_rejection_hits += 1
            else:
                false_positive = True
                false_positive_retrievals += 1
        else:
            target_file = tc.get("expected_file")
            target_page = tc.get("expected_page")

            for rank, node in enumerate(retrieved_nodes):
                meta = node.metadata or {}
                src = meta.get("source_file") or meta.get("manual_name") or ""
                p = meta.get("page_number")

                if target_file and (target_file.lower() in src.lower() or src.lower() in target_file.lower()):
                    if rank < 3:
                        hit_k3 = True
                    if rank < 5:
                        hit_k5 = True
                    if target_page and p == target_page:
                        page_match = True

            if hit_k3:
                retrieval_hits_k3 += 1
            if hit_k5:
                retrieval_hits_k5 += 1
            if page_match:
                citation_page_matches += 1

        top_score = retrieved_nodes[0].score if retrieved_nodes else 0.0
        passed_gate = len(qualified_nodes) > 0

        status_str = "REJECTED (Correct)" if (is_neg and neg_rejected) else (
            "HIT (Top-3)" if hit_k3 else ("HIT (Top-5)" if hit_k5 else ("REJECTED (FP)" if false_positive else "MISS"))
        )
        print(f"[{i:02d}/{len(EVAL_CASES)}] {tc['id']} | Top-Score: {top_score:.3f} | Gate: {'PASS' if passed_gate else 'BLOCKED'} | {status_str} | '{q[:40]}...'")

        results.append({
            "id": tc["id"],
            "query": q,
            "category": tc["category"],
            "is_negative": is_neg,
            "latency_s": round(elapsed, 3),
            "top_score": round(top_score, 3) if top_score is not None else None,
            "passed_grounding_gate": passed_gate,
            "hit_k3": hit_k3,
            "hit_k5": hit_k5,
            "page_match": page_match,
            "neg_rejected": neg_rejected,
            "false_positive": false_positive,
            "top_source": retrieved_nodes[0].metadata.get("source_file") if retrieved_nodes else None,
            "top_page": retrieved_nodes[0].metadata.get("page_number") if retrieved_nodes else None
        })

    recall_k3 = (retrieval_hits_k3 / total_positives) * 100 if total_positives else 0
    recall_k5 = (retrieval_hits_k5 / total_positives) * 100 if total_positives else 0
    page_acc = (citation_page_matches / total_positives) * 100 if total_positives else 0
    neg_rate = (negative_rejection_hits / total_negatives) * 100 if total_negatives else 0
    hallucination_risk = (false_positive_retrievals / total_negatives) * 100 if total_negatives else 0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0

    print(f"\n=======================================================")
    print(f"BENCHMARK EMPIRICAL RESULTS SUMMARY (N = {len(EVAL_CASES)})")
    print(f"=======================================================")
    print(f"Positive Test Cases:         {total_positives}")
    print(f"Negative (OOD) Test Cases:   {total_negatives}")
    print(f"Retrieval Recall@3:          {recall_k3:.1f}% ({retrieval_hits_k3}/{total_positives})")
    print(f"Retrieval Recall@5:          {recall_k5:.1f}% ({retrieval_hits_k5}/{total_positives})")
    print(f"Citation Page Accuracy:      {page_acc:.1f}% ({citation_page_matches}/{total_positives})")
    print(f"Negative Rejection Rate:     {neg_rate:.1f}% ({negative_rejection_hits}/{total_negatives})")
    print(f"Hallucination Risk (FP):     {hallucination_risk:.1f}% ({false_positive_retrievals}/{total_negatives})")
    print(f"Avg Retrieval Latency:       {avg_latency * 1000:.1f} ms")
    print(f"=======================================================\n")

    summary_data = {
        "metrics": {
            "total_cases": len(EVAL_CASES),
            "positives": total_positives,
            "negatives": total_negatives,
            "recall_k3_pct": round(recall_k3, 1),
            "recall_k5_pct": round(recall_k5, 1),
            "page_citation_accuracy_pct": round(page_acc, 1),
            "negative_rejection_rate_pct": round(neg_rate, 1),
            "hallucination_risk_pct": round(hallucination_risk, 1),
            "avg_retrieval_latency_ms": round(avg_latency * 1000, 1)
        },
        "individual_runs": results
    }

    out_json = project_root / "data" / "benchmark_results.json"
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    print(f"Benchmark results saved to: {out_json}")

    return summary_data

if __name__ == "__main__":
    run_evaluation_suite()
