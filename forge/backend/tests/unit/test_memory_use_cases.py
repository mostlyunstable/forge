"""Unit tests for Memory use cases."""

import pytest

from forge.application.memory.delete_bug import DeleteBugUseCase
from forge.application.memory.delete_decision import DeleteDecisionUseCase
from forge.application.memory.delete_preference import DeletePreferenceUseCase
from forge.application.memory.get_bug import GetBugUseCase
from forge.application.memory.get_decision import GetDecisionUseCase
from forge.application.memory.get_preferences import GetPreferencesUseCase
from forge.application.memory.list_bugs import ListBugsUseCase
from forge.application.memory.list_decisions import ListDecisionsUseCase
from forge.application.memory.save_bug import SaveBugRequest, SaveBugUseCase
from forge.application.memory.save_decision import SaveDecisionRequest, SaveDecisionUseCase
from forge.application.memory.save_preference import SavePreferenceRequest, SavePreferenceUseCase
from forge.application.memory.update_bug import UpdateBugRequest, UpdateBugUseCase
from forge.application.memory.update_decision import UpdateDecisionRequest, UpdateDecisionUseCase
from forge.domain.memory.exceptions import BugNotFoundError, DecisionNotFoundError
from forge.domain.projects.exceptions import ProjectNotFoundError


class TestSaveDecisionUseCase:
    @pytest.mark.asyncio
    async def test_save_decision(self, decision_repo, project_repo, sample_project):
        use_case = SaveDecisionUseCase(decision_repo, project_repo)
        result = await use_case.execute(
            SaveDecisionRequest(
                project_id=str(sample_project.id.value),
                title="Use PostgreSQL",
                decision="Use PostgreSQL for the database",
                reason="It's reliable",
                alternatives=["MySQL", "SQLite"],
            )
        )
        assert result.title == "Use PostgreSQL"
        assert result.decision == "Use PostgreSQL for the database"

    @pytest.mark.asyncio
    async def test_save_decision_project_not_found(self, decision_repo, project_repo):
        use_case = SaveDecisionUseCase(decision_repo, project_repo)
        with pytest.raises(ProjectNotFoundError):
            await use_case.execute(
                SaveDecisionRequest(
                    project_id="00000000-0000-0000-0000-000000000000",
                    title="Test",
                    decision="Test",
                    reason="Test",
                )
            )

    @pytest.mark.asyncio
    async def test_save_decision_publishes_event(
        self, decision_repo, project_repo, sample_project, event_bus
    ):
        use_case = SaveDecisionUseCase(decision_repo, project_repo, event_bus=event_bus)
        await use_case.execute(
            SaveDecisionRequest(
                project_id=str(sample_project.id.value),
                title="Event Test",
                decision="Test",
                reason="Test",
            )
        )
        events = event_bus.get_published()
        assert len(events) == 1
        assert events[0].event_type == "decision.recorded"


class TestGetDecisionUseCase:
    @pytest.mark.asyncio
    async def test_get_decision(self, decision_repo, sample_decision):
        use_case = GetDecisionUseCase(decision_repo)
        result = await use_case.execute(str(sample_decision.id))
        assert result.title == "Use FastAPI"

    @pytest.mark.asyncio
    async def test_get_decision_not_found(self, decision_repo):
        use_case = GetDecisionUseCase(decision_repo)
        with pytest.raises(DecisionNotFoundError):
            await use_case.execute("00000000-0000-0000-0000-000000000000")


class TestListDecisionsUseCase:
    @pytest.mark.asyncio
    async def test_list_decisions(
        self, decision_repo, project_repo, sample_project, sample_decision
    ):
        use_case = ListDecisionsUseCase(decision_repo, project_repo)
        result = await use_case.execute(str(sample_project.id.value))
        assert result.total == 1
        assert result.decisions[0].title == "Use FastAPI"

    @pytest.mark.asyncio
    async def test_list_decisions_project_not_found(self, decision_repo, project_repo):
        use_case = ListDecisionsUseCase(decision_repo, project_repo)
        with pytest.raises(ProjectNotFoundError):
            await use_case.execute("00000000-0000-0000-0000-000000000000")


class TestUpdateDecisionUseCase:
    @pytest.mark.asyncio
    async def test_update_decision(self, decision_repo, sample_decision):
        use_case = UpdateDecisionUseCase(decision_repo)
        result = await use_case.execute(
            UpdateDecisionRequest(
                decision_id=str(sample_decision.id),
                title="Updated Title",
            )
        )
        assert result.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_decision_not_found(self, decision_repo):
        use_case = UpdateDecisionUseCase(decision_repo)
        with pytest.raises(DecisionNotFoundError):
            await use_case.execute(
                UpdateDecisionRequest(
                    decision_id="00000000-0000-0000-0000-000000000000",
                    title="Test",
                )
            )


class TestDeleteDecisionUseCase:
    @pytest.mark.asyncio
    async def test_delete_decision(self, decision_repo, sample_decision):
        use_case = DeleteDecisionUseCase(decision_repo)
        result = await use_case.execute(str(sample_decision.id))
        assert result.deleted is True

    @pytest.mark.asyncio
    async def test_delete_decision_not_found(self, decision_repo):
        use_case = DeleteDecisionUseCase(decision_repo)
        with pytest.raises(DecisionNotFoundError):
            await use_case.execute("00000000-0000-0000-0000-000000000000")

    @pytest.mark.asyncio
    async def test_delete_publishes_event(self, decision_repo, sample_decision, event_bus):
        use_case = DeleteDecisionUseCase(decision_repo, event_bus=event_bus)
        await use_case.execute(str(sample_decision.id))
        events = event_bus.get_published()
        assert len(events) == 1
        assert events[0].event_type == "decision.deleted"


class TestSaveBugUseCase:
    @pytest.mark.asyncio
    async def test_save_bug(self, bug_repo, project_repo, sample_project):
        use_case = SaveBugUseCase(bug_repo, project_repo)
        result = await use_case.execute(
            SaveBugRequest(
                project_id=str(sample_project.id.value),
                title="SQL injection",
                problem="User input not sanitized",
                root_cause="Missing parameterized queries",
                solution="Use ORM",
                severity="critical",
            )
        )
        assert result.title == "SQL injection"
        assert result.severity == "critical"

    @pytest.mark.asyncio
    async def test_save_bug_publishes_event(
        self, bug_repo, project_repo, sample_project, event_bus
    ):
        use_case = SaveBugUseCase(bug_repo, project_repo, event_bus=event_bus)
        await use_case.execute(
            SaveBugRequest(
                project_id=str(sample_project.id.value),
                title="Event Test",
                problem="Test",
                root_cause="Test",
                solution="Test",
            )
        )
        events = event_bus.get_published()
        assert len(events) == 1
        assert events[0].event_type == "bug.recorded"


class TestGetBugUseCase:
    @pytest.mark.asyncio
    async def test_get_bug(self, bug_repo, sample_bug):
        use_case = GetBugUseCase(bug_repo)
        result = await use_case.execute(str(sample_bug.id))
        assert result.title == "Null pointer"

    @pytest.mark.asyncio
    async def test_get_bug_not_found(self, bug_repo):
        use_case = GetBugUseCase(bug_repo)
        with pytest.raises(BugNotFoundError):
            await use_case.execute("00000000-0000-0000-0000-000000000000")


class TestListBugsUseCase:
    @pytest.mark.asyncio
    async def test_list_bugs(self, bug_repo, project_repo, sample_project, sample_bug):
        use_case = ListBugsUseCase(bug_repo, project_repo)
        result = await use_case.execute(str(sample_project.id.value))
        assert result.total == 1
        assert result.bugs[0].title == "Null pointer"


class TestUpdateBugUseCase:
    @pytest.mark.asyncio
    async def test_update_bug(self, bug_repo, sample_bug):
        use_case = UpdateBugUseCase(bug_repo)
        result = await use_case.execute(
            UpdateBugRequest(
                bug_id=str(sample_bug.id),
                title="Updated Title",
            )
        )
        assert result.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_mark_resolved(self, bug_repo, sample_bug, event_bus):
        # Bug.create() sets resolved=True by default, so mark it unresolved first
        sample_bug.mark_unresolved()
        await bug_repo.save(sample_bug)
        event_bus.clear()

        use_case = UpdateBugUseCase(bug_repo, event_bus=event_bus)
        result = await use_case.execute(
            UpdateBugRequest(
                bug_id=str(sample_bug.id),
                resolved=True,
            )
        )
        assert result.resolved is True
        events = event_bus.get_published()
        assert any(e.event_type == "bug.resolved" for e in events)


class TestDeleteBugUseCase:
    @pytest.mark.asyncio
    async def test_delete_bug(self, bug_repo, sample_bug):
        use_case = DeleteBugUseCase(bug_repo)
        result = await use_case.execute(str(sample_bug.id))
        assert result.deleted is True

    @pytest.mark.asyncio
    async def test_delete_publishes_event(self, bug_repo, sample_bug, event_bus):
        use_case = DeleteBugUseCase(bug_repo, event_bus=event_bus)
        await use_case.execute(str(sample_bug.id))
        events = event_bus.get_published()
        assert len(events) == 1
        assert events[0].event_type == "bug.deleted"


class TestSavePreferenceUseCase:
    @pytest.mark.asyncio
    async def test_save_new_preference(self, preference_repo):
        use_case = SavePreferenceUseCase(preference_repo)
        result = await use_case.execute(
            SavePreferenceRequest(
                key="testing",
                value="pytest",
                confidence=0.9,
            )
        )
        assert result.key == "testing"
        assert result.value == "pytest"

    @pytest.mark.asyncio
    async def test_strengthen_existing_preference(self, preference_repo, sample_preference):
        use_case = SavePreferenceUseCase(preference_repo)
        result = await use_case.execute(
            SavePreferenceRequest(
                key="code_style",
                value="black",
            )
        )
        assert result.evidence_count == 2
        assert result.confidence > 0.8


class TestDeletePreferenceUseCase:
    @pytest.mark.asyncio
    async def test_delete_preference(self, preference_repo, sample_preference):
        use_case = DeletePreferenceUseCase(preference_repo)
        result = await use_case.execute("code_style")
        assert result.deleted is True

    @pytest.mark.asyncio
    async def test_delete_publishes_event(self, preference_repo, sample_preference, event_bus):
        use_case = DeletePreferenceUseCase(preference_repo, event_bus=event_bus)
        await use_case.execute("code_style")
        events = event_bus.get_published()
        assert len(events) == 1
        assert events[0].event_type == "preference.deleted"


class TestGetPreferencesUseCase:
    @pytest.mark.asyncio
    async def test_get_preferences(self, preference_repo, sample_preference):
        use_case = GetPreferencesUseCase(preference_repo)
        result = await use_case.execute()
        assert result.total == 1
