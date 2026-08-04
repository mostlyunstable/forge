import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session


class Exporter:
    def __init__(self, session: Session):
        self.session = session

    def export_conversations_to_sharegpt(self, output_path: str, min_rating: int = 0):
        """
        Exports all conversations in the database to a ShareGPT formatted JSONL file.
        ShareGPT format:
        {"conversations": [{"from": "human", "value": "..."}, {"from": "gpt", "value": "..."}]}
        """
        from forge.infrastructure.database.models.conversation_model import ConversationModel

        # Query all conversations
        conversations = self.session.execute(select(ConversationModel)).scalars().all()

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        exported_count = 0
        with open(output_file, "w", encoding="utf-8") as f:
            for conv in conversations:
                # We need at least a human and gpt pair to be useful
                if len(conv.messages) < 2:
                    continue

                # Check rating
                if min_rating > 0:
                    try:
                        meta = json.loads(str(conv.metadata_))
                        rating = meta.get("rating", 0)
                        if rating < min_rating:
                            continue
                    except Exception:
                        continue

                exported_count += 1

                # Sort messages by created_at (assuming order is preserved in DB relationship)
                sorted_messages = sorted(conv.messages, key=lambda m: m.created_at)

                sharegpt_msgs = []
                for msg in sorted_messages:
                    # ShareGPT uses "human", "gpt", "system"
                    role_map = {"user": "human", "assistant": "gpt", "system": "system"}
                    sharegpt_msgs.append(
                        {"from": role_map.get(msg.role, msg.role), "value": msg.content}
                    )

                jsonl_line = json.dumps({"conversations": sharegpt_msgs})
                f.write(jsonl_line + "\n")

        return exported_count
