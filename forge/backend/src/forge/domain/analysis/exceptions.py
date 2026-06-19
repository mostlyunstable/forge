"""Exceptions for the analysis bounded context."""


class AnalysisReportNotFoundError(Exception):
    """Raised when an analysis report is not found."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"Analysis report not found: {identifier}")


class AnalysisError(Exception):
    """Raised when PR analysis fails."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(f"Analysis failed: {reason}")
