import asyncio
import json
import os
import sys
from pathlib import Path

# Setup Python Path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from forge.infrastructure.llm.llm_service import LLMService
from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.application.conversation.token_manager import ContextWindow
from forge.domain.conversation.entities.message import Message

async def run_evals():
    llm_service = LLMService()
    if not llm_service.is_configured:
        print("❌ Error: LLM API key not configured. Set GROQ_API_KEY.")
        sys.exit(1)

    engine = ReasoningEngine(llm_service)
    
    tasks_file = Path(__file__).parent / "benchmark_tasks.json"
    if not tasks_file.exists():
        print(f"❌ Error: Could not find {tasks_file}")
        sys.exit(1)
        
    tasks = json.loads(tasks_file.read_text())
    
    print("=" * 60)
    print(f"🚀 FORGE EVALUATION HARNESS - {len(tasks)} TASKS")
    print("=" * 60)
    
    total_score = 0
    total_possible = 0

    for i, task in enumerate(tasks, 1):
        print(f"\n[Task {i}/{len(tasks)}] {task['id']}")
        print(f"Prompt: {task['prompt']}")
        
        cw = ContextWindow(
            summary="",
            summary_tokens=0,
            messages=[],
            message_tokens=0,
            total_tokens=0
        )
        
        final_text = ""
        tool_calls = 0
        
        try:
            async for chunk in engine.generate_response_stream(
                context_window=cw,
                retrieved_context="",
                user_prompt=task['prompt']
            ):
                if isinstance(chunk, dict):
                    if chunk["type"] == "status":
                        print(f"  ⚙️  {chunk['message']}")
                        tool_calls += 1
                    elif chunk["type"] == "text":
                        final_text += chunk["content"]
                else:
                    final_text += str(chunk)
        except Exception as e:
            print(f"\n❌ Execution Error: {e}")
            final_text += f"\n[Error: {e}]"
                
        print("\n--- Output ---")
        print(final_text.strip())
        print("--------------")
        
        # Scoring
        score = 0
        expected = task.get("expected_concepts", [])
        for concept in expected:
            total_possible += 1
            if concept.lower() in final_text.lower():
                score += 1
                total_score += 1
                print(f"✅ Concept hit: {concept}")
            else:
                # If they asked for a tool, check if it used tools
                if "tool" in concept.lower() or "shell" in concept.lower():
                    if tool_calls > 0:
                        score += 1
                        total_score += 1
                        print(f"✅ Concept hit (Tool usage detected): {concept}")
                        continue
                print(f"❌ Concept missed: {concept}")
                
        print(f"Score for {task['id']}: {score}/{len(expected)}")
        
    print("\n" + "=" * 60)
    print(f"🏆 FINAL EVALUATION SCORE: {total_score}/{total_possible} ({(total_score/total_possible)*100:.1f}%)")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_evals())
