"""Unit tests for Projects use cases."""
import pytest
from forge.domain.projects.entities.project import Project
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.domain.projects.value_objects.tech_stack import TechStack
from forge.domain.projects.exceptions import ProjectNotFoundError, ProjectAlreadyExistsError
from forge.application.projects.create_project import CreateProjectUseCase, CreateProjectRequest
from forge.application.projects.get_project import GetProjectUseCase
from forge.application.projects.list_projects import ListProjectsUseCase
from forge.application.projects.update_project import UpdateProjectUseCase, UpdateProjectRequest
from forge.application.projects.delete_project import DeleteProjectUseCase


class TestCreateProjectUseCase:
    @pytest.mark.asyncio
    async def test_create_project(self, project_repo):
        use_case = CreateProjectUseCase(project_repo)
        result = await use_case.execute(CreateProjectRequest(
            name="My Project",
            description="Test",
            stack=["python"],
            goals=["Goal 1"],
        ))
        assert result.name == "My Project"
        assert result.description == "Test"
        assert result.stack == ["python"]
        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_create_project_duplicate_name(self, project_repo, sample_project):
        use_case = CreateProjectUseCase(project_repo)
        with pytest.raises(ProjectAlreadyExistsError):
            await use_case.execute(CreateProjectRequest(
                name="Test Project",
                description="Duplicate",
                stack=[],
            ))

    @pytest.mark.asyncio
    async def test_create_project_publishes_event(self, project_repo, event_bus):
        use_case = CreateProjectUseCase(project_repo, event_bus=event_bus)
        await use_case.execute(CreateProjectRequest(
            name="Event Test",
            description="",
            stack=[],
        ))
        events = event_bus.get_published()
        assert len(events) == 1
        assert events[0].event_type == "project.created"


class TestGetProjectUseCase:
    @pytest.mark.asyncio
    async def test_get_project(self, project_repo, sample_project):
        use_case = GetProjectUseCase(project_repo)
        result = await use_case.execute(str(sample_project.id.value))
        assert result.name == "Test Project"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, project_repo):
        use_case = GetProjectUseCase(project_repo)
        with pytest.raises(ProjectNotFoundError):
            await use_case.execute("00000000-0000-0000-0000-000000000000")


class TestListProjectsUseCase:
    @pytest.mark.asyncio
    async def test_list_empty(self, project_repo):
        use_case = ListProjectsUseCase(project_repo)
        result = await use_case.execute()
        assert result.total == 0
        assert result.projects == []

    @pytest.mark.asyncio
    async def test_list_with_projects(self, project_repo, sample_project):
        use_case = ListProjectsUseCase(project_repo)
        result = await use_case.execute()
        assert result.total == 1
        assert result.projects[0].name == "Test Project"

    @pytest.mark.asyncio
    async def test_list_pagination(self, project_repo):
        for i in range(5):
            p = Project.create(
                name=f"Project {i}",
                description="",
                stack=TechStack.from_list([]),
            )
            await project_repo.save(p)
        use_case = ListProjectsUseCase(project_repo)
        result = await use_case.execute(skip=1, limit=2)
        assert result.total == 2
        assert len(result.projects) == 2


class TestUpdateProjectUseCase:
    @pytest.mark.asyncio
    async def test_update_description(self, project_repo, sample_project):
        use_case = UpdateProjectUseCase(project_repo)
        result = await use_case.execute(UpdateProjectRequest(
            project_id=str(sample_project.id.value),
            description="Updated description",
        ))
        assert result.description == "Updated description"

    @pytest.mark.asyncio
    async def test_update_stack(self, project_repo, sample_project):
        use_case = UpdateProjectUseCase(project_repo)
        result = await use_case.execute(UpdateProjectRequest(
            project_id=str(sample_project.id.value),
            stack=["rust", "go"],
        ))
        assert set(result.stack) == {"rust", "go"}

    @pytest.mark.asyncio
    async def test_update_not_found(self, project_repo):
        use_case = UpdateProjectUseCase(project_repo)
        with pytest.raises(ProjectNotFoundError):
            await use_case.execute(UpdateProjectRequest(
                project_id="00000000-0000-0000-0000-000000000000",
                description="test",
            ))

    @pytest.mark.asyncio
    async def test_update_publishes_event(self, project_repo, sample_project, event_bus):
        use_case = UpdateProjectUseCase(project_repo, event_bus=event_bus)
        await use_case.execute(UpdateProjectRequest(
            project_id=str(sample_project.id.value),
            description="Updated",
        ))
        events = event_bus.get_published()
        assert len(events) == 1
        assert events[0].event_type == "project.updated"


class TestDeleteProjectUseCase:
    @pytest.mark.asyncio
    async def test_delete_project(self, project_repo, sample_project):
        use_case = DeleteProjectUseCase(project_repo)
        result = await use_case.execute(str(sample_project.id.value))
        assert result.deleted is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self, project_repo):
        use_case = DeleteProjectUseCase(project_repo)
        with pytest.raises(ProjectNotFoundError):
            await use_case.execute("00000000-0000-0000-0000-000000000000")

    @pytest.mark.asyncio
    async def test_delete_publishes_event(self, project_repo, sample_project, event_bus):
        use_case = DeleteProjectUseCase(project_repo, event_bus=event_bus)
        await use_case.execute(str(sample_project.id.value))
        events = event_bus.get_published()
        assert len(events) == 1
        assert events[0].event_type == "project.deleted"
