"""
Agentic Analytics Agent powered by Ollama.
Orchestrates multi-step reasoning to turn raw data into actionable insights.
"""

import json
import re
import time
from typing import Any, Generator
import ollama
import pandas as pd

from backend.analytics.engine import AnalyticsEngine
from backend.data.loader import DataLoader
from backend.utils.logger import get_logger

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are an expert data analyst AI agent. Your role is to:
1. Understand user questions about their data.
2. Plan a step-by-step analysis strategy.
3. Execute analysis using available tools.
4. Generate clear, actionable insights with supporting evidence.
5. Recommend next steps or further investigation.

Always structure your responses with:
- **Summary**: One-sentence answer.
- **Analysis**: Detailed findings backed by numbers.
- **Insights**: Key takeaways and patterns.
- **Recommendations**: Actionable next steps.

You have access to the following tools:
- describe_data(dataset_id): Get schema and summary statistics.
- run_query(dataset_id, query): Run a natural language query on a dataset.
- detect_anomalies(dataset_id, column): Detect outliers and anomalies.
- trend_analysis(dataset_id, column, time_col): Analyze trends over time.
- correlate(dataset_id, col_a, col_b): Compute correlation between two columns.
- segment(dataset_id, column): Perform value segmentation/grouping.
- forecast(dataset_id, column, time_col, periods): Forecast future values.

To call a tool, output a JSON block exactly like:
```tool_call
{"tool": "tool_name", "args": {"arg1": "value1"}}
```
After receiving tool results, continue reasoning until you can give a complete answer.
"""


class AnalyticsAgent:
    """
    Agentic loop that uses Ollama LLM + tool calling to analyze data
    and produce real-time streaming insights.
    """

    def __init__(self, model: str = "llama3.2", max_iterations: int = 10):
        self.model = model
        self.max_iterations = max_iterations
        self.engine = AnalyticsEngine()
        self.loader = DataLoader()
        self.tools = {
            "describe_data": self._tool_describe_data,
            "run_query": self._tool_run_query,
            "detect_anomalies": self._tool_detect_anomalies,
            "trend_analysis": self._tool_trend_analysis,
            "correlate": self._tool_correlate,
            "segment": self._tool_segment,
            "forecast": self._tool_forecast,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def chat(
        self,
        user_message: str,
        dataset_id: str | None = None,
        history: list[dict] | None = None,
        stream: bool = True,
    ) -> Generator[dict, None, None]:
        """
        Run the agentic loop and yield streaming events.

        Yields dicts with keys:
          - type: "thinking" | "tool_call" | "tool_result" | "answer" | "done" | "error"
          - content: str or dict
        """
        messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        if history:
            messages.extend(history)

        context = f"\n\n[Active dataset: {dataset_id}]" if dataset_id else ""
        messages.append({"role": "user", "content": user_message + context})

        for iteration in range(self.max_iterations):
            yield {"type": "thinking", "content": f"Iteration {iteration + 1}: calling LLM..."}

            try:
                response = ollama.chat(
                    model=self.model,
                    messages=messages,
                    stream=False,
                )
            except Exception as exc:
                yield {"type": "error", "content": str(exc)}
                return

            assistant_msg = response["message"]["content"]
            messages.append({"role": "assistant", "content": assistant_msg})

            # Check for tool calls
            tool_call = self._extract_tool_call(assistant_msg)
            if tool_call:
                tool_name = tool_call.get("tool")
                tool_args = tool_call.get("args", {})
                yield {"type": "tool_call", "content": {"tool": tool_name, "args": tool_args}}

                result = self._execute_tool(tool_name, tool_args)
                yield {"type": "tool_result", "content": result}

                messages.append({
                    "role": "user",
                    "content": f"[Tool result for {tool_name}]:\n{json.dumps(result, default=str)}",
                })
                continue

            # No tool call — final answer
            yield {"type": "answer", "content": assistant_msg}
            yield {"type": "done", "content": {"iterations": iteration + 1}}
            return

        yield {"type": "answer", "content": "Maximum reasoning iterations reached. Here is my best analysis based on available information."}
        yield {"type": "done", "content": {"iterations": self.max_iterations}}

    def quick_analyze(self, dataset_id: str) -> dict:
        """Run an automatic full analysis on a dataset."""
        events = list(self.chat(
            f"Perform a comprehensive analysis of dataset '{dataset_id}'. "
            "Describe the data, find key trends, detect anomalies, and provide top 3 business insights.",
            dataset_id=dataset_id,
            stream=False,
        ))
        answer_events = [e for e in events if e["type"] == "answer"]
        return {
            "dataset_id": dataset_id,
            "answer": answer_events[-1]["content"] if answer_events else "",
            "events": events,
        }

    # ------------------------------------------------------------------
    # Tool Implementations
    # ------------------------------------------------------------------

    def _tool_describe_data(self, dataset_id: str) -> dict:
        try:
            df = self.loader.load(dataset_id)
            return self.engine.describe(df)
        except Exception as e:
            return {"error": str(e)}

    def _tool_run_query(self, dataset_id: str, query: str) -> dict:
        try:
            df = self.loader.load(dataset_id)
            return self.engine.natural_language_query(df, query)
        except Exception as e:
            return {"error": str(e)}

    def _tool_detect_anomalies(self, dataset_id: str, column: str) -> dict:
        try:
            df = self.loader.load(dataset_id)
            return self.engine.detect_anomalies(df, column)
        except Exception as e:
            return {"error": str(e)}

    def _tool_trend_analysis(self, dataset_id: str, column: str, time_col: str) -> dict:
        try:
            df = self.loader.load(dataset_id)
            return self.engine.trend_analysis(df, column, time_col)
        except Exception as e:
            return {"error": str(e)}

    def _tool_correlate(self, dataset_id: str, col_a: str, col_b: str) -> dict:
        try:
            df = self.loader.load(dataset_id)
            return self.engine.correlate(df, col_a, col_b)
        except Exception as e:
            return {"error": str(e)}

    def _tool_segment(self, dataset_id: str, column: str) -> dict:
        try:
            df = self.loader.load(dataset_id)
            return self.engine.segment(df, column)
        except Exception as e:
            return {"error": str(e)}

    def _tool_forecast(self, dataset_id: str, column: str, time_col: str, periods: int = 7) -> dict:
        try:
            df = self.loader.load(dataset_id)
            return self.engine.forecast(df, column, time_col, periods)
        except Exception as e:
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_tool_call(self, text: str) -> dict | None:
        pattern = r"```tool_call\s*(\{.*?\})\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                return None
        return None

    def _execute_tool(self, tool_name: str, args: dict) -> Any:
        if tool_name not in self.tools:
            return {"error": f"Unknown tool: {tool_name}"}
        try:
            return self.tools[tool_name](**args)
        except Exception as e:
            logger.error(f"Tool execution error [{tool_name}]: {e}")
            return {"error": str(e)}
