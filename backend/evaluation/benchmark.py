import json
import time
import os
from typing import List, Dict, Any

# Dummy vector store retriever for demonstration purposes.
# In the real system, this would import the Forge Vector Store and call its retrieve method.
def mock_retrieve(query: str, top_k: int = 10) -> List[Dict[str, Any]]:
    # Mocking a response with some files
    # This should be replaced with actual vector store logic
    return [
        {"filepath": "backend/vector_store/connection.py", "content": "mock content", "citation_valid": True, "hallucinated": False},
        {"filepath": "backend/pipeline/embedding.py", "content": "mock content", "citation_valid": True, "hallucinated": False},
        {"filepath": "backend/database/schema.sql", "content": "mock content", "citation_valid": False, "hallucinated": True}
    ][:top_k]

def calculate_precision_at_k(retrieved_files: List[str], ground_truth_files: List[str], k: int) -> float:
    retrieved_k = retrieved_files[:k]
    if not retrieved_k:
        return 0.0
    relevant = set(retrieved_k).intersection(set(ground_truth_files))
    return len(relevant) / k

def calculate_recall_at_k(retrieved_files: List[str], ground_truth_files: List[str], k: int) -> float:
    retrieved_k = retrieved_files[:k]
    if not ground_truth_files:
        return 0.0
    relevant = set(retrieved_k).intersection(set(ground_truth_files))
    return len(relevant) / len(ground_truth_files)

def calculate_mrr(retrieved_files: List[str], ground_truth_files: List[str]) -> float:
    for i, filepath in enumerate(retrieved_files):
        if filepath in ground_truth_files:
            return 1.0 / (i + 1)
    return 0.0

def run_benchmark(questions_file: str, ground_truth_file: str):
    print("Loading benchmark data...")
    with open(questions_file, 'r') as f:
        questions = json.load(f)
        
    with open(ground_truth_file, 'r') as f:
        ground_truth = json.load(f)

    total_precision_5 = 0.0
    total_recall_10 = 0.0
    total_mrr = 0.0
    total_latency = 0.0
    total_citations = 0
    valid_citations = 0
    total_hallucinations = 0
    total_retrieved = 0

    print(f"Running evaluation for {len(questions)} questions...")
    
    for q in questions:
        q_id = q["id"]
        query = q["question"]
        expected_files = ground_truth.get(q_id, [])

        start_time = time.time()
        # In a real scenario, top_k should be at least 10 for Recall@10
        results = mock_retrieve(query, top_k=10)
        latency = time.time() - start_time
        total_latency += latency

        retrieved_files = [res["filepath"] for res in results]
        
        # Metrics
        total_precision_5 += calculate_precision_at_k(retrieved_files, expected_files, 5)
        total_recall_10 += calculate_recall_at_k(retrieved_files, expected_files, 10)
        total_mrr += calculate_mrr(retrieved_files, expected_files)
        
        # Citation & Hallucination metrics based on mock flags
        for res in results:
            total_citations += 1
            if res.get("citation_valid", False):
                valid_citations += 1
            if res.get("hallucinated", False):
                total_hallucinations += 1
            total_retrieved += 1

    num_q = len(questions)
    
    avg_precision_5 = total_precision_5 / num_q if num_q > 0 else 0
    avg_recall_10 = total_recall_10 / num_q if num_q > 0 else 0
    avg_mrr = total_mrr / num_q if num_q > 0 else 0
    avg_latency = (total_latency / num_q) * 1000 # ms
    
    citation_validity = (valid_citations / total_citations) * 100 if total_citations > 0 else 0
    hallucination_rate = (total_hallucinations / total_retrieved) * 100 if total_retrieved > 0 else 0

    print("\n" + "="*40)
    print(" Forge Phase 1 - Retrieval Benchmark ")
    print("="*40)
    print(f"Total Questions    : {num_q}")
    print(f"Precision@5        : {avg_precision_5:.4f}")
    print(f"Recall@10          : {avg_recall_10:.4f}")
    print(f"MRR                : {avg_mrr:.4f}")
    print(f"Citation Validity  : {citation_validity:.2f}%")
    print(f"Hallucination Rate : {hallucination_rate:.2f}%")
    print(f"Average Latency    : {avg_latency:.2f} ms")
    print("="*40)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    questions_path = os.path.join(base_dir, "questions.json")
    ground_truth_path = os.path.join(base_dir, "ground_truth.json")
    
    if not os.path.exists(questions_path) or not os.path.exists(ground_truth_path):
        print("Error: questions.json or ground_truth.json not found in the same directory.")
    else:
        run_benchmark(questions_path, ground_truth_path)
