import json
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select

from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import Message

class Exporter:
    def __init__(self, session: Session):
        self.session = session

    def export_conversations_to_sharegpt(self, output_path: str):
        """
        Exports all conversations in the database to a ShareGPT formatted JSONL file.
        ShareGPT format:
        {"conversations": [{"from": "human", "value": "..."}, {"from": "gpt", "value": "..."}]}
        """
        from forge.infrastructure.database.models.conversation_model import ConversationModel
        from forge.infrastructure.database.models.message_model import MessageModel
        
        # Query all conversations
        conversations = self.session.execute(select(ConversationModel)).scalars().all()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for conv in conversations:
                # We need at least a human and gpt pair to be useful
                if len(conv.messages) < 2:
                    continue
                
                # Sort messages by created_at (assuming order is preserved in DB relationship)
                sorted_messages = sorted(conv.messages, key=lambda m: m.created_at)
                
                sharegpt_msgs = []
                for msg in sorted_messages:
                    # ShareGPT uses "human", "gpt", "system"
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
                
        return len(conversations)
