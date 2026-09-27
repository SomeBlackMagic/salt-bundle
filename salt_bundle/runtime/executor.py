"""Parallel execution for independent runtime groups."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from salt_bundle.runtime.backends.base import (
    ExecutionResult,
    RuntimeBackend,
    RuntimeContext,
    SaltCommand,
)
from salt_bundle.runtime.grouping import RuntimeGroup


@dataclass
class GroupExecutionResult:
    """The outcome of one isolated runtime group invocation."""

    group: RuntimeGroup
    results: list[ExecutionResult]
    success: bool
    error: Exception | None


@dataclass
class ParallelExecutionResult:
    """The aggregated outcome of all runtime group invocations."""

    group_results: list[GroupExecutionResult]

    @property
    def success(self) -> bool:
        """Return whether every group completed successfully."""
        return all(group_result.success for group_result in self.group_results)

    @property
    def exit_code(self) -> int:
        """Return the execution exit code."""
        return 0 if self.success else 1


def execute_parallel(
    groups: dict[str, RuntimeGroup],
    backend: RuntimeBackend,
    context: RuntimeContext,
    command: SaltCommand,
    *,
    max_workers: int = 4,
) -> ParallelExecutionResult:
    """Prepare and execute independent runtime groups concurrently."""
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            pool.submit(_execute_group, group, backend, context, command)
            for group in groups.values()
        ]
        group_results = [future.result() for future in futures]
    return ParallelExecutionResult(group_results=group_results)


def _execute_group(
    group: RuntimeGroup,
    backend: RuntimeBackend,
    context: RuntimeContext,
    command: SaltCommand,
) -> GroupExecutionResult:
    """Execute one group and turn backend failures into a group result."""
    try:
        prepared = backend.prepare(group.targets, group.manifest, context)
        results = list(backend.execute(prepared, command))
    except Exception as error:
        return GroupExecutionResult(
            group=group,
            results=[],
            success=False,
            error=error,
        )
    return GroupExecutionResult(
        group=group,
        results=results,
        success=all(result.success for result in results),
        error=None,
    )
