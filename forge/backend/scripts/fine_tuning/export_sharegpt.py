import asyncio
import sys
from pathlib import Path

# Setup Python Path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from forge.infrastructure.database.connection import database_manager
from forge.infrastructure.training.exporter import Exporter

async def run_export(output_path: str):
    async with database_manager.get_session() as db:
        exporter = Exporter(db)
        # Note: Exporter currently uses synchronous SQLalchemy select,
        # but since database_manager provides an async session, we need
        # to ensure the models are eagerly loaded or accessed properly.
        # Let's adjust for async:
        from forge.infrastructure.database.models.conversation_model import ConversationModel
        from forge.infrastructure.database.models.message_model import MessageModel
        from forge.infrastructure.database.models.conversation_session_model import ConversationSessionModel
        from forge.infrastructure.database.models.conversation_summary_model import ConversationSummaryModel
        from forge.infrastructure.database.models.conversation_citation_model import ConversationCitationModel
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        result = await db.execute(
            select(ConversationModel).options(selectinload(ConversationModel.messages))
        )
        conversations = result.scalars().all()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        count = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for conv in conversations:
                if len(conv.messages) < 2:
                    continue
                
                sorted_messages = sorted(conv.messages, key=lambda m: m.created_at)
                
                sharegpt_msgs = []
                for msg in sorted_messages:
                    role_map = {
                        "user": "human",
                        "assistant": "gpt",
                        "system": "system"
                    }
                    sharegpt_msgs.append({
                        "from": role_map.get(msg.role, msg.role),
                        "value": msg.content
                    })
                    
                jsonl_line = json.dumps({"conversations": sharegpt_msgs})
                f.write(jsonl_line + "\n")
                count += 1
                
        print(f"✅ Exported {count} conversations to {output_path} in ShareGPT format.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        output_file = "dataset.jsonl"
    else:
        output_file = sys.argv[1]
        
    asyncio.run(run_export(output_file))
