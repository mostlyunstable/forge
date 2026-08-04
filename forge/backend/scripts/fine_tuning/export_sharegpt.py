import asyncio
import sys
from pathlib import Path

# Setup Python Path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from forge.infrastructure.database.connection import database_manager
from forge.infrastructure.training.exporter import Exporter


async def run_export(output_path: str, min_rating: int = 0):
    async with database_manager.get_session() as db:
        # Note: Exporter currently uses synchronous SQLalchemy select,
        # but since database_manager provides an async session, we need
        # to ensure the models are eagerly loaded or accessed properly.
        # Let's adjust for async:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from forge.infrastructure.database.models.conversation_model import ConversationModel

        result = await db.execute(
            select(ConversationModel).options(selectinload(ConversationModel.messages))
        )
        conversations = result.scalars().all()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        import json

        count = 0
        with open(output_file, "w", encoding="utf-8") as f:
            for conv in conversations:
                if len(conv.messages) < 2:
                    continue

                if min_rating > 0:
                    try:
                        meta = json.loads(str(conv.metadata_))
                        rating = meta.get("rating", 0)
                        if rating < min_rating:
                            continue
                    except Exception:
                        continue

                sorted_messages = sorted(conv.messages, key=lambda m: m.created_at)

                sharegpt_msgs = []
                for msg in sorted_messages:
                    role_map = {"user": "human", "assistant": "gpt", "system": "system"}
                    sharegpt_msgs.append(
                        {"from": role_map.get(msg.role, msg.role), "value": msg.content}
                    )

                jsonl_line = json.dumps({"conversations": sharegpt_msgs})
                f.write(jsonl_line + "\n")
                count += 1

        print(f"✅ Exported {count} conversations to {output_path} in ShareGPT format.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export conversations to ShareGPT format.")
    parser.add_argument(
        "output_file", nargs="?", default="dataset.jsonl", help="Output JSONL file path"
    )
    parser.add_argument(
        "--min-rating", type=int, default=0, help="Minimum rating (1-5) to include in export"
    )
    args = parser.parse_args()

    asyncio.run(run_export(args.output_file, args.min_rating))
