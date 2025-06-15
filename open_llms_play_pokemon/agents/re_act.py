import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import dspy
from dspy.adapters.types.tool import Tool
from dspy.primitives.program import Module
from dspy.signatures.signature import ensure_signature
from litellm.exceptions import ContextWindowExceededError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from dspy.signatures.signature import Signature


class ReAct(Module):
    def __init__(
        self, signature: type["Signature"], tools: list[Callable], max_iters: int = 10
    ):
        """
        ReAct stands for "Reasoning and Acting," a popular paradigm for building tool-using agents.
        In this approach, the language model is iteratively provided with a list of tools and has
        to reason about the current situation. The model decides whether to call a tool to gather more
        information or to finish the task based on its reasoning process. The DSPy version of ReAct is
        generalized to work over any signature, thanks to signature polymorphism.

        Args:
            signature: The signature of the module, which defines the input and output of the react module.
            tools (list[Callable]): A list of functions, callable objects, or `dspy.Tool` instances.
            max_iters (Optional[int]): The maximum number of iterations to run. Defaults to 10.

        Example:

        ```python
        def get_weather(city: str) -> str:
            return f"The weather in {city} is sunny."

        react = dspy.ReAct(signature="question->answer", tools=[get_weather])
        pred = react(question="What is the weather in Tokyo?")
        ```
        """
        super().__init__()
        self.signature = ensure_signature(signature)
        self.max_iters = max_iters

        tool_instances = [t if isinstance(t, Tool) else Tool(t) for t in tools]
        tools_dict = {tool.name: tool for tool in tool_instances}

        inputs = ", ".join([f"`{k}`" for k in signature.input_fields.keys()])
        outputs = ", ".join([f"`{k}`" for k in signature.output_fields.keys()])
        instr = [f"{signature.instructions}\n"] if signature.instructions else []

        instr.extend(
            [
                f"You are an Agent. In each episode, you will be given the fields {inputs} as input. And you can see your past trajectory so far.",
                f"Your goal is to use one or more of the supplied tools to collect any necessary information for producing {outputs}.\n",
                "To do this, you will interleave next_thought, next_tool_name, and next_tool_args in each turn, and also when finishing the task.",
                "After each tool call, you receive a resulting observation, which gets appended to your trajectory.\n",
                "When writing next_thought, you may reason about the current situation and plan for future steps.",
                "When selecting the next_tool_name and its next_tool_args, the tool must be one of:\n",
            ]
        )

        tools_dict["finish"] = Tool(
            func=lambda: "Completed.",
            name="finish",
            desc=f"Marks the task as complete. That is, signals that all information for producing the outputs, i.e. {outputs}, are now available to be extracted.",
            args={},
        )

        for idx, tool in enumerate(tools_dict.values()):
            instr.append(f"({idx + 1}) {tool}")
        instr.append(
            "When providing `next_tool_args`, the value inside the field must be in JSON format"
        )

        # Create signature string from input fields
        input_field_names = list(signature.input_fields.keys())
        signature_str = f"{', '.join(input_field_names)}, trajectory -> next_thought, next_tool_name, next_tool_args"

        react_signature = dspy.Signature(signature_str)  # type: ignore[call-arg]

        # Create fallback signature string
        output_field_names = list(signature.output_fields.keys())
        fallback_signature_str = f"{', '.join(input_field_names)}, trajectory -> {', '.join(output_field_names)}"

        fallback_signature = dspy.Signature(fallback_signature_str)  # type: ignore[call-arg]

        self.tools = tools_dict
        self.react = dspy.Predict(react_signature)  # type: ignore[arg-type]
        self.extract = dspy.ChainOfThought(fallback_signature)  # type: ignore[arg-type]

    def _format_trajectory(self, trajectory: dict[str, Any]) -> str:
        adapter = dspy.settings.adapter or dspy.ChatAdapter()
        trajectory_signature_str = f"{', '.join(trajectory.keys())} -> x"
        trajectory_signature = dspy.Signature(trajectory_signature_str)  # type: ignore[call-arg]
        return adapter.format_user_message_content(trajectory_signature, trajectory)  # type: ignore[arg-type]

    def forward(self, **input_args):
        trajectory = {}
        max_iters = input_args.pop("max_iters", self.max_iters)
        for idx in range(max_iters):
            try:
                pred = self._call_with_potential_trajectory_truncation(
                    self.react, trajectory, **input_args
                )
            except ValueError as err:
                logger.warning(
                    f"Ending the trajectory: Agent failed to select a valid tool: {_fmt_exc(err)}"
                )
                break

            if pred is None:
                logger.warning("Prediction returned None, ending trajectory")
                break

            trajectory[f"thought_{idx}"] = getattr(pred, "next_thought", "")
            trajectory[f"tool_name_{idx}"] = getattr(pred, "next_tool_name", "finish")
            trajectory[f"tool_args_{idx}"] = getattr(pred, "next_tool_args", {})

            tool_name = getattr(pred, "next_tool_name", "finish")
            tool_args = getattr(pred, "next_tool_args", {})

            try:
                tool = self.tools.get(tool_name)
                if tool is not None:
                    trajectory[f"observation_{idx}"] = tool(**tool_args)
                else:
                    trajectory[f"observation_{idx}"] = f"Tool '{tool_name}' not found"
            except Exception as err:
                trajectory[f"observation_{idx}"] = (
                    f"Execution error in {tool_name}: {_fmt_exc(err)}"
                )

            if tool_name == "finish":
                break

        extract = self._call_with_potential_trajectory_truncation(
            self.extract, trajectory, **input_args
        )
        if extract is None:
            extract = dspy.Prediction()

        # Create result with trajectory and extracted fields
        result_dict = {"trajectory": trajectory}
        if hasattr(extract, "__dict__"):
            result_dict.update(
                {k: v for k, v in extract.__dict__.items() if not k.startswith("_")}
            )

        return dspy.Prediction(**result_dict)

    async def aforward(self, **input_args):
        trajectory = {}
        max_iters = input_args.pop("max_iters", self.max_iters)
        for idx in range(max_iters):
            try:
                pred = await self._async_call_with_potential_trajectory_truncation(
                    self.react, trajectory, **input_args
                )
            except ValueError as err:
                logger.warning(
                    f"Ending the trajectory: Agent failed to select a valid tool: {_fmt_exc(err)}"
                )
                break

            if pred is None:
                logger.warning("Prediction returned None, ending trajectory")
                break

            trajectory[f"thought_{idx}"] = getattr(pred, "next_thought", "")
            trajectory[f"tool_name_{idx}"] = getattr(pred, "next_tool_name", "finish")
            trajectory[f"tool_args_{idx}"] = getattr(pred, "next_tool_args", {})

            tool_name = getattr(pred, "next_tool_name", "finish")
            tool_args = getattr(pred, "next_tool_args", {})

            try:
                tool = self.tools.get(tool_name)
                if tool is not None:
                    trajectory[f"observation_{idx}"] = await tool.acall(**tool_args)
                else:
                    trajectory[f"observation_{idx}"] = f"Tool '{tool_name}' not found"
            except Exception as err:
                trajectory[f"observation_{idx}"] = (
                    f"Execution error in {tool_name}: {_fmt_exc(err)}"
                )

            if tool_name == "finish":
                break

        extract = await self._async_call_with_potential_trajectory_truncation(
            self.extract, trajectory, **input_args
        )
        if extract is None:
            extract = dspy.Prediction()

        # Create result with trajectory and extracted fields
        result_dict = {"trajectory": trajectory}
        if hasattr(extract, "__dict__"):
            result_dict.update(
                {k: v for k, v in extract.__dict__.items() if not k.startswith("_")}
            )

        return dspy.Prediction(**result_dict)

    def _call_with_potential_trajectory_truncation(
        self, module, trajectory, **input_args
    ) -> Any:
        for _ in range(3):
            try:
                return module(
                    **input_args,
                    trajectory=self._format_trajectory(trajectory),
                )
            except ContextWindowExceededError:
                logger.warning(
                    "Trajectory exceeded the context window, truncating the oldest tool call information."
                )
                trajectory = self.truncate_trajectory(trajectory)
        raise RuntimeError("Failed to execute module after 3 attempts")

    async def _async_call_with_potential_trajectory_truncation(
        self, module, trajectory, **input_args
    ) -> Any:
        for _ in range(3):
            try:
                return await module.acall(
                    **input_args,
                    trajectory=self._format_trajectory(trajectory),
                )
            except ContextWindowExceededError:
                logger.warning(
                    "Trajectory exceeded the context window, truncating the oldest tool call information."
                )
                trajectory = self.truncate_trajectory(trajectory)
        raise RuntimeError("Failed to execute async module after 3 attempts")

    def truncate_trajectory(self, trajectory):
        """Truncates the trajectory so that it fits in the context window.

        Users can override this method to implement their own truncation logic.
        """
        keys = list(trajectory.keys())
        if len(keys) < 4:
            # Every tool call has 4 keys: thought, tool_name, tool_args, and observation.
            raise ValueError(
                "The trajectory is too long so your prompt exceeded the context window, but the trajectory cannot be "
                "truncated because it only has one tool call."
            )

        for key in keys[:4]:
            trajectory.pop(key)

        return trajectory


def _fmt_exc(err: BaseException, *, limit: int = 5) -> str:
    """
    Return a one-string traceback summary.
    * `limit` - how many stack frames to keep (from the innermost outwards).
    """

    import traceback

    return (
        "\n"
        + "".join(
            traceback.format_exception(type(err), err, err.__traceback__, limit=limit)
        ).strip()
    )


"""
Thoughts and Planned Improvements for dspy.ReAct.

TOPIC 01: How Trajectories are Formatted, or rather when they are formatted.

Right now, both sub-modules are invoked with a `trajectory` argument, which is a string formatted in `forward`. Though
the formatter uses a general adapter.format_fields, the tracing of DSPy only sees the string, not the formatting logic.

What this means is that, in demonstrations, even if the user adjusts the adapter for a fixed program, the demos' format
will not update accordingly, but the inference-time trajectories will.

One way to fix this is to support `format=fn` in the dspy.InputField() for "trajectory" in the signatures. But this
means that care must be taken that the adapter is accessed at `forward` runtime, not signature definition time.

Another potential fix is to more natively support a "variadic" input field, where the input is a list of dictionaries,
or a big dictionary, and have each adatper format it accordingly.

Trajectories also affect meta-programming modules that view the trace later. It's inefficient O(n^2) to view the
trace of every module repeating the prefix.


TOPIC 03: Simplifying ReAct's __init__ by moving modular logic to the Tool class.
    * Handling exceptions and error messages.
    * More cleanly defining the "finish" tool, perhaps as a runtime-defined function?


TOPIC 04: Default behavior when the trajectory gets too long.


TOPIC 05: Adding more structure around how the instruction is formatted.
    * Concretely, it's now a string, so an optimizer can and does rewrite it freely.
    * An alternative would be to add more structure, such that a certain template is fixed but values are variable?


TOPIC 06: Idiomatically allowing tools that maintain state across iterations, but not across different `forward` calls.
    * So the tool would be newly initialized at the start of each `forward` call, but maintain state across iterations.
    * This is pretty useful for allowing the agent to keep notes or count certain things, etc.
"""
