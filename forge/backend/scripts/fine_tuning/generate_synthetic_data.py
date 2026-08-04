import asyncio
import random
import sys
from pathlib import Path

import structlog

# Setup Python Path
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir / "src"))

from datetime import UTC

from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.entities.message import Message
from forge.infrastructure.database.connection import database_manager
from forge.infrastructure.llm.llm_service import LLMService
from forge.infrastructure.repositories.conversation_repository import ConversationRepository

logger = structlog.get_logger()

PROMPTS = [
    "How does the IntentRouter work?",
    "Explain the architecture of the ReasoningEngine.",
    "Why do we use SQLite instead of PostgreSQL?",
    "What is the purpose of the KnowledgeIngester?",
    "Show me how to run the fine-tuning export script.",
    "How is context memory handled in the ConversationContextManager?",
    "Can you explain the Reciprocal Rank Fusion implementation?",
]


async def generate_synthetic_data():
    logger.info("Starting synthetic data generation loop... (Press Ctrl+C to stop)")

    # Initialize services
    llm_service = LLMService()

    while True:
        try:
            async with database_manager.get_session() as db:
                repo = ConversationRepository(db)

                # Ensure a project exists
                from sqlalchemy import select

                from forge.infrastructure.database.models.project_model import ProjectModel

                result = await db.execute(select(ProjectModel).limit(1))
                project_model = result.scalar_one_or_none()
                if not project_model:
                    from datetime import datetime

                    from forge.domain.projects.value_objects.project_id import ProjectId

                    project_id = ProjectId()
                    new_project = ProjectModel(
                        id=str(project_id.value),
                        name="Synthetic Project",
                        created_at=datetime.now(UTC),
                        updated_at=datetime.now(UTC),
                    )
                    db.add(new_project)
                    await db.commit()
                else:
                    import uuid

                    from forge.domain.projects.value_objects.project_id import ProjectId

                    project_id = ProjectId(uuid.UUID(project_model.id))

                # Start a new conversation
                conv = Conversation.create(project_id=project_id, title="Synthetic Conversation")

                # 1. Simulate User Message
                user_prompt = random.choice(PROMPTS)
                user_msg = Message.create_user(conversation_id=conv.id, content=user_prompt)
                conv.add_message(user_msg)

                logger.info(f"Generated user prompt: {user_prompt}")

                # 2. Simulate Assistant Message
                system_prompt = "You are Forge, an AI Engineering Companion. Answer the user's question clearly and concisely based on the Forge architecture."
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                logger.info("Generating assistant response...")
                response = await llm_service.chat(messages=messages, max_tokens=500)

                assistant_msg = Message.create_assistant(
                    conversation_id=conv.id, content=response.content
                )
                conv.add_message(assistant_msg)

                # 3. Simulate User Rating (4 or 5 stars for high quality dataset)
                rating = random.choice([4, 5])
                conv.metadata["rating"] = rating

                # Save to database
                await repo.save(conv)
                logger.info(f"✅ Saved synthetic conversation {conv.id.value} with rating {rating}")

            # Wait a bit before generating the next one
            await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.info("Stopping generation loop.")
            break
        except Exception as e:
            logger.error(f"Error during generation: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(generate_synthetic_data())
    except KeyboardInterrupt:
        print("\nStopped synthetic data generation.")
