from forge.domain.agent.agent_profile import AgentProfile


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, AgentProfile] = {}

    def register(self, profile: AgentProfile) -> None:
        self._agents[profile.name] = profile

    def get(self, name: str) -> AgentProfile | None:
        return self._agents.get(name)

    def list_agents(self) -> list[AgentProfile]:
        return list(self._agents.values())

    def load_defaults(self) -> None:
        orchestrator = AgentProfile(
            name="forge_orchestrator",
            role="Forge AI Swarm Orchestrator",
            system_prompt_template="""You are the master Forge Orchestrator. 
Your goal is to understand the user's intent, break it down, and delegate complex tasks to specialized agents like 'code_debugger' and 'researcher'. 
When you need help with code issues, use the 'delegate_task' tool to send tasks to 'code_debugger'.
When you need to search or crawl the codebase for context, send tasks to 'researcher'.
Otherwise, if the task is simple, answer it directly using your own reasoning.""",
            allowed_tools=[
                "delegate_task",
                "search_web",
                "read_file",
                "write_file",
                "run_shell_command",
            ],
        )

        debugger = AgentProfile(
            name="code_debugger",
            role="Expert Code Debugger",
            system_prompt_template="""You are a specialized Python debugging agent. 
You are invoked by the orchestrator to solve specific bugs. You have full access to run shell commands, 
run pytest, and edit files. Work methodically to find and fix the problem, then return a detailed summary of your fixes.""",
            allowed_tools=["read_file", "write_file", "run_shell_command", "run_python_code"],
        )

        researcher = AgentProfile(
            name="researcher",
            role="Codebase Researcher",
            system_prompt_template="""You are a specialized Codebase Researcher agent. 
You are invoked by the orchestrator to explore directories, read files, and search the codebase. 
Gather the requested information and summarize it clearly.""",
            allowed_tools=["read_file", "run_shell_command"],
        )

        self.register(orchestrator)
        self.register(debugger)
        self.register(researcher)
