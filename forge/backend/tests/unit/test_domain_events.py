"""Tests for domain events infrastructure."""
import pytest
from forge.domain.shared.events import DomainEvent
from forge.domain.projects.events import ProjectCreated, ProjectUpdated, ProjectDeleted
from forge.domain.memory.events import DecisionRecorded, BugRecorded, PreferenceRecorded
from forge.domain.code.events import CodeEntriesBatchIndexed
from forge.infrastructure.events.in_memory_event_bus import InMemoryEventBus


class FakeHandler:
    """Test handler that records events it receives."""

    def __init__(self, event_type: str = "project.created"):
        self.event_type = event_type
        self.events: list[DomainEvent] = []

    async def handle(self, event: DomainEvent) -> None:
        self.events.append(event)


class TestDomainEvents:
    def test_project_created_event(self):
        event = ProjectCreated(project_id="123", project_name="Test")
        assert event.event_type == "project.created"
        assert event.project_id == "123"
        assert event.project_name == "Test"
        assert event.event_id is not None
        assert event.occurred_at is not None

    def test_event_to_dict(self):
        event = ProjectCreated(project_id="123", project_name="Test")
        d = event.to_dict()
        assert d["event_type"] == "project.created"
        assert d["project_id"] == "123"
        assert d["project_name"] == "Test"
        assert "event_id" in d
        assert "occurred_at" in d

    def test_decision_recorded_event(self):
        event = DecisionRecorded(
            decision_id="d1", project_id="p1", title="Use FastAPI"
        )
        assert event.event_type == "decision.recorded"
        assert event.decision_id == "d1"

    def test_bug_recorded_event(self):
        event = BugRecorded(bug_id="b1", project_id="p1", title="Null pointer")
        assert event.event_type == "bug.recorded"

    def test_code_batch_indexed_event(self):
        event = CodeEntriesBatchIndexed(
            project_id="p1", entry_count=42, repo_path="/src"
        )
        assert event.event_type == "code.batch_indexed"
        assert event.entry_count == 42


class TestInMemoryEventBus:
    @pytest.mark.asyncio
    async def test_publish_event(self):
        bus = InMemoryEventBus()
        handler = FakeHandler("project.created")
        bus.register(handler)

        event = ProjectCreated(project_id="123", project_name="Test")
        await bus.publish(event)

        assert len(handler.events) == 1
        assert handler.events[0].event_type == "project.created"

    @pytest.mark.asyncio
    async def test_publish_many_events(self):
        bus = InMemoryEventBus()
        handler = FakeHandler("project.created")
        bus.register(handler)

        events = [
            ProjectCreated(project_id="1", project_name="A"),
            ProjectCreated(project_id="2", project_name="B"),
        ]
        await bus.publish_many(events)

        assert len(handler.events) == 2

    @pytest.mark.asyncio
    async def test_wildcard_handler(self):
        bus = InMemoryEventBus()

        class WildcardHandler:
            event_type = "*"
            events = []
            async def handle(self, event):
                self.events.append(event)

        handler = WildcardHandler()
        bus.register(handler)

        await bus.publish(ProjectCreated(project_id="1", project_name="A"))
        await bus.publish(BugRecorded(bug_id="b1", project_id="p1", title="X"))

        assert len(handler.events) == 2

    @pytest.mark.asyncio
    async def test_no_handlers_does_not_crash(self):
        bus = InMemoryEventBus()
        event = ProjectCreated(project_id="1", project_name="A")
        await bus.publish(event)  # Should not raise

    @pytest.mark.asyncio
    async def test_handler_error_does_not_stop_others(self):
        bus = InMemoryEventBus()

        class FailingHandler:
            event_type = "project.created"
            async def handle(self, event):
                raise RuntimeError("boom")

        class GoodHandler:
            event_type = "project.created"
            events = []
            async def handle(self, event):
                self.events.append(event)

        bus.register(FailingHandler())
        good = GoodHandler()
        bus.register(good)

        await bus.publish(ProjectCreated(project_id="1", project_name="A"))
        assert len(good.events) == 1

    @pytest.mark.asyncio
    async def test_get_published(self):
        bus = InMemoryEventBus()
        await bus.publish(ProjectCreated(project_id="1", project_name="A"))
        published = bus.get_published()
        assert len(published) == 1

    @pytest.mark.asyncio
    async def test_clear(self):
        bus = InMemoryEventBus()
        await bus.publish(ProjectCreated(project_id="1", project_name="A"))
        bus.clear()
        assert len(bus.get_published()) == 0
