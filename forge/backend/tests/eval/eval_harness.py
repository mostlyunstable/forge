import asyncio
import json
import sys
from pathlib import Path

# Setup Python Path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.application.conversation.token_manager import ContextWindow
from forge.infrastructure.llm.llm_service import LLMService


import argparse

from forge.application.agent.tools import ForgeTools, set_tools_base_dir

async def run_evals():
    parser = argparse.ArgumentParser(description="Forge AI Evaluation Harness")
    parser.add_argument("--filter", type=str, help="Run only tasks matching this ID substring")
    args = parser.parse_args()

    set_tools_base_dir(backend_dir)

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
    
    if args.filter:
        tasks = [t for t in tasks if args.filter in t["id"]]

    print("=" * 60)
    print(f"🚀 FORGE EVALUATION HARNESS - {len(tasks)} TASKS")
    print("=" * 60)

    total_score = 0
    total_possible = 0
    report_lines = [
        "# Forge Evaluation Report",
        f"**Total Tasks:** {len(tasks)}\n",
        "## Task Details"
    ]

    for i, task in enumerate(tasks, 1):
        print(f"\n[Task {i}/{len(tasks)}] {task['id']}")
        print(f"Prompt: {task['prompt']}")

        cw = ContextWindow(
            summary="", summary_tokens=0, messages=[], message_tokens=0, total_tokens=0
        )

        final_text = ""
        tool_calls = 0

        try:
            async for chunk in engine.generate_response_stream(
                context_window=cw, retrieved_context="", user_prompt=task["prompt"]
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

        # LLM-as-a-Judge Scoring
        expected = task.get("expected_concepts", [])
        judge_prompt = f"""
You are an expert software engineering judge evaluating an AI assistant.
The user asked the following prompt:
{task["prompt"]}

The AI assistant produced this output:
{final_text.strip()}

The assistant should ideally cover these expected concepts: {", ".join(expected)}

Rate the AI assistant's response on a scale of 1 to 5, where:
1: Completely wrong or failed to answer.
2: Poor, missed major concepts.
3: Average, covered some concepts but missed others.
4: Good, covered most concepts accurately.
5: Excellent, perfect coverage of all concepts.

Return ONLY the integer score (1, 2, 3, 4, or 5). Do not include any other text.
"""
        try:
            judge_response = await llm_service.chat([{"role": "user", "content": judge_prompt}])
            try:
                score = int(judge_response.content.strip())
            except ValueError:
                print(f"⚠️ Judge returned non-integer: {judge_response.content}. Defaulting to 1.")
                score = 1
        except Exception as e:
            print(f"❌ Judge LLM Failed: {e}")
            score = 1

        total_possible += 5
        total_score += score

        print(f"Score for {task['id']}: {score}/5")
        
        report_lines.extend([
            f"\n### {task['id']}",
            f"**Prompt:** {task['prompt']}",
            f"**Score:** {score}/5",
            f"**Tool Calls:** {tool_calls}",
            "**Output:**",
            f"```text\n{final_text.strip()}\n```",
            "---"
        ])

    final_percentage = (total_score / total_possible) * 100 if total_possible > 0 else 0
    print("\n" + "=" * 60)
    print(
        f"🏆 FINAL EVALUATION SCORE: {total_score}/{total_possible} ({final_percentage:.1f}%)"
    )
    print("=" * 60)
    
    report_lines.insert(1, f"**Final Score:** {total_score}/{total_possible} ({final_percentage:.1f}%)\n")
    
    report_path = Path(__file__).parent / "eval_report.md"
    report_path.write_text("\n".join(report_lines))
    print(f"📄 Report written to {report_path.resolve()}")


if __name__ == "__main__":
    asyncio.run(run_evals())
