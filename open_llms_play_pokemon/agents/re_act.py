import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

import dspy

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from dspy.signatures.signature import Signature


class ReAct(dspy.Module):
    def __init__(
        self, signature: type["Signature"], tools: list[Callable], max_iters: int = 10
    ):
        """
        Custom ReAct implementation that delegates to DSPy's ReAct for performance.

        This is essentially a wrapper around dspy.ReAct that maintains the same
        interface while allowing for potential customizations in the future.
        """
        super().__init__()

        # Just delegate to the standard DSPy ReAct implementation
        self._dspy_react = dspy.ReAct(signature, tools, max_iters)

        # Store parameters for potential future customization
        self.signature = signature
        self.tools = tools
        self.max_iters = max_iters

    def forward(self, **kwargs):
        """Forward pass that delegates to DSPy's ReAct."""
        return self._dspy_react.forward(**kwargs)

    def __call__(self, **kwargs):
        """Make the module callable."""
        return self.forward(**kwargs)

    async def aforward(self, **kwargs):
        """Async forward pass."""
        return await self._dspy_react.aforward(**kwargs)
