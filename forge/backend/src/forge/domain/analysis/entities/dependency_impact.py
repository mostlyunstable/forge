"""DependencyImpact — which modules are affected by changes."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DependencyImpact:
    """Maps changed files to their dependency impact."""

    directly_affected: list[str] = field(default_factory=list)
    transitively_affected: list[str] = field(default_factory=list)
    reverse_affected: list[str] = field(default_factory=list)
    import_edges: list[dict] = field(default_factory=list)
    cycle_detected: bool = False
    affected_layers: list[str] = field(default_factory=list)

    @property
    def total_affected_modules(self) -> int:
        """Count of unique affected modules across all categories."""
        all_modules = set(self.directly_affected) | set(self.transitively_affected) | set(self.reverse_affected)
        return len(all_modules)

    @property
    def blast_radius(self) -> int:
        """Blast radius score: higher means more impact.

        Scoring:
        - Directly affected: 3 points each
        - Transitively affected: 2 points each
        - Reverse affected (dependents): 4 points each (highest — breakage propagates here)
        - Cycle detected: +20 bonus
        """
        score = (
            len(self.directly_affected) * 3
            + len(self.transitively_affected) * 2
            + len(self.reverse_affected) * 4
        )
        if self.cycle_detected:
            score += 20
        return score

    @property
    def layers_affected_summary(self) -> str:
        return ", ".join(sorted(self.affected_layers)) if self.affected_layers else "none"
