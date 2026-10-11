"""The five-agent PydanticAI team and its shared, depth-limited run context."""
from dataclasses import dataclass, field
import asyncio
from pathlib import Path
from typing import Any
from uuid import uuid4
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext, RunUsage, UsageLimits
from pydantic_ai.mcp import MCPToolset, StdioTransport
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.toolsets import FilteredToolset
from .audit import event
from .config import PROJECT_ROOT, MODEL_NAME, PORTKEY_API_KEY, PORTKEY_BASE_URL, MAX_DELEGATION_DEPTH, MAX_REQUESTS, MAX_TOTAL_TOKENS

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
ROLES = ("boss", "inventory", "accounting", "facilities", "customer_service")
MAX_DELEGATIONS_PER_RUN = 6
MAX_DELEGATIONS = MAX_DELEGATIONS_PER_RUN
ROLE_FILES = {role: PROMPT_DIR / f"{role}.md" for role in ROLES}

@dataclass
class RunBudget:
    delegation_attempts: int = 0
    delegation_successes: int = 0
    delegation_keys: set[tuple[str, str, str]] = field(default_factory=set)
    returned_models: set[tuple[str, str | None]] = field(default_factory=set)
    event_step: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def next_step(self) -> int:
        self.event_step += 1
        return self.event_step

@dataclass
class RunContextData:
    run_id: str
    ticket_id: int
    session_id: str | None = None
    depth: int = 0
    step: int = 0
    usage_limits: UsageLimits = field(default_factory=lambda: UsageLimits(request_limit=MAX_REQUESTS, total_tokens_limit=MAX_TOTAL_TOKENS))
    usage: RunUsage = field(default_factory=RunUsage)
    delegation_stack: list[str] = field(default_factory=list)
    budget: RunBudget = field(default_factory=RunBudget)
    def next_step(self) -> int:
        return self.budget.next_step()


async def delegate_with_budget(data: RunContextData, sender: str, recipient: str, task: str, runner):
    """Reserve a delegation against the single run-wide budget, then execute its child."""
    recipient = recipient.strip().lower().replace(" ", "_")
    key = (sender, recipient, " ".join(task.lower().split()))
    async with data.budget.lock:
        data.budget.delegation_attempts += 1
        if recipient not in AGENTS:
            return "Delegation refused: unknown agent role."
        if recipient == sender:
            return "Delegation refused: an agent cannot delegate to itself."
        if recipient in data.delegation_stack:
            return f"Delegation refused: {recipient} is already on this delegation path; return your findings instead of delegating back."
        if data.budget.delegation_successes >= MAX_DELEGATIONS_PER_RUN:
            return "Delegation refused: this run already used the six-delegation limit; finish with the evidence you have."
        if key in data.budget.delegation_keys:
            return "Delegation refused: this same task was already delegated to that agent in this run; use the answer you received."
        if data.depth >= MAX_DELEGATION_DEPTH:
            return "Delegation refused: maximum delegation depth reached; return the findings already gathered."
        data.budget.delegation_successes += 1
        data.budget.delegation_keys.add(key)
    child = RunContextData(
        run_id=data.run_id,
        ticket_id=data.ticket_id,
        session_id=data.session_id,
        depth=data.depth + 1,
        usage_limits=data.usage_limits,
        usage=data.usage,
        delegation_stack=data.delegation_stack + [sender],
        budget=data.budget,
    )
    return await runner(recipient, task, child)

class RunStoppedError(RuntimeError):
    """Unwinds every parent agent when a shared run limit is reached."""

def model() -> OpenAIResponsesModel:
    client = AsyncOpenAI(api_key=PORTKEY_API_KEY, base_url=PORTKEY_BASE_URL, default_headers={"x-portkey-api-key": PORTKEY_API_KEY})
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))

def usage_dict(usage) -> dict[str, int | float]:
    keys = ("requests", "input_tokens", "output_tokens", "total_tokens", "cache_read_tokens", "cache_write_tokens")
    result = {key: int(getattr(usage, key, 0) or 0) for key in keys}
    cost = getattr(usage, "cost", None)
    if cost is not None:
        result["cost"] = float(cost)
    return result

def mcp_toolset() -> FilteredToolset:
    server = MCPToolset(StdioTransport(str(PROJECT_ROOT / ".venv" / "bin" / "python"), [str(PROJECT_ROOT / "mcp_server" / "server.py")]))
    blocked = {"execute_approved_payment", "reject_payment_request", "record_human_decision", "set_ticket_status"}
    return FilteredToolset(server, lambda _ctx, tool: tool.name not in blocked)

AGENTS: dict[str, Agent[RunContextData, str]] = {}

def make_agent(role: str) -> Agent[RunContextData, str]:
    agent = Agent(model(), name=role, deps_type=RunContextData, system_prompt=ROLE_FILES[role].read_text(), toolsets=[mcp_toolset()], model_settings={"max_tokens": 1200})

    @agent.tool
    async def delegate(ctx: RunContext[RunContextData], to_agent: str, task: str) -> str:
        """Delegate to one of boss, inventory, accounting, facilities, or customer_service."""
        data = ctx.deps
        normalized = to_agent.strip().lower().replace(" ", "_")
        event(data.run_id, data.next_step(), role, "delegation_requested", data.ticket_id, {"to_agent": normalized, "task": task, "depth": data.depth}, session_id=data.session_id)
        try:
            answer = await delegate_with_budget(data, role, normalized, task, run_agent)
            if answer.startswith("Delegation refused:"):
                event(data.run_id, data.next_step(), role, "delegation_refused", data.ticket_id, {"to_agent": normalized, "task": task, "reason": answer}, "refused", data.session_id)
                return answer
            event(data.run_id, data.next_step(), role, "delegation_result", data.ticket_id, {"to_agent": to_agent, "result": str(answer)[:4000]}, session_id=data.session_id)
            return str(answer)
        except RunStoppedError:
            raise
        except Exception as exc:
            event(data.run_id, data.next_step(), role, "delegation_error", data.ticket_id, {"to_agent": to_agent, "error": str(exc)}, "error", data.session_id)
            return f"Delegated task failed safely: {exc}"
    return agent

for _role in ROLES:
    AGENTS[_role] = make_agent(_role)

async def run_agent(role: str, task: str, data: RunContextData) -> str:
    event(data.run_id, data.next_step(), role, "loop_start", data.ticket_id, {"task": task, "depth": data.depth}, session_id=data.session_id)
    try:
        async with AGENTS[role].iter(
            task, deps=data, usage=data.usage, usage_limits=data.usage_limits
        ) as agent_run:
            async for node in agent_run:
                node_name = type(node).__name__
                if node_name == "ModelRequestNode":
                    request = getattr(node, "request", None)
                    parts = getattr(request, "parts", [])
                    event(data.run_id, data.next_step(), role, "model_request", data.ticket_id,
                          {"parts": [type(part).__name__ for part in parts if "SystemPrompt" not in type(part).__name__]}, session_id=data.session_id)
                    for part in parts:
                        if "ToolReturnPart" in type(part).__name__:
                            event(data.run_id, data.next_step(), role, "tool_result", data.ticket_id,
                                  {"tool_name": getattr(part, "tool_name", None), "tool_call_id": getattr(part, "tool_call_id", None), "result": _event_text(getattr(part, "content", ""))}, session_id=data.session_id)
                elif node_name == "CallToolsNode":
                    response = getattr(node, "model_response", None)
                    identity = {
                        "model_name": getattr(response, "model_name", None),
                        "provider_name": getattr(response, "provider_name", None),
                    }
                    data.budget.returned_models.add((identity["model_name"] or "unknown", identity["provider_name"]))
                    texts = [str(getattr(part, "content", "")) for part in getattr(response, "parts", []) if "TextPart" in type(part).__name__]
                    event(data.run_id, data.next_step(), role, "model_response", data.ticket_id,
                          {"text": _event_text(" ".join(texts)), "returned_model": identity}, session_id=data.session_id)
                    for part in getattr(response, "parts", []):
                        if "ToolCallPart" in type(part).__name__:
                            event(data.run_id, data.next_step(), role, "tool_call", data.ticket_id,
                                  {"tool_name": getattr(part, "tool_name", None), "args": _event_value(getattr(part, "args", None)), "tool_call_id": getattr(part, "tool_call_id", None)}, session_id=data.session_id)
        result = agent_run.result
        if result is None:
            raise RuntimeError("Agent iteration ended without a final result.")
        output = str(result.output)
        final_detail = {
            "result": output[:8000],
            "usage": usage_dict(result.usage),
            "delegation_attempts": data.budget.delegation_attempts,
            "delegation_successes": data.budget.delegation_successes,
        }
        if role == "boss":
            identities = sorted(data.budget.returned_models, key=lambda item: (item[0], item[1] or ""))
            returned_models = [
                {"model_name": model_name, "provider_name": provider_name}
                for model_name, provider_name in identities
            ]
            final_detail["returned_models"] = returned_models
            final_detail["returned_models_line"] = "Returned models: " + ", ".join(
                f"{item['model_name']}" + (f" via {item['provider_name']}" if item["provider_name"] else "")
                for item in returned_models
            )
        event(data.run_id, data.next_step(), role, "final_output", data.ticket_id, final_detail, session_id=data.session_id)
        event(data.run_id, data.next_step(), role, "token_usage", data.ticket_id, {"usage": usage_dict(data.usage)}, session_id=data.session_id)
        return output
    except Exception as exc:
        if type(exc).__name__ == "UsageLimitExceeded":
            event(data.run_id, data.next_step(), role, "usage_limit_exceeded", data.ticket_id, {"message": str(exc), "usage": usage_dict(data.usage)}, "limit", data.session_id)
            raise RunStoppedError(f"Shared run limit reached while {role} was working: {exc}") from exc
        event(data.run_id, data.next_step(), role, "loop_error", data.ticket_id, {"error": str(exc)}, "error", data.session_id)
        raise

async def run_ticket(ticket_id: int, *, run_id: str | None = None, session_id: str | None = None) -> str:
    data = RunContextData(run_id or str(uuid4()), ticket_id, session_id=session_id)
    return await run_agent("boss", f"Review open ticket {ticket_id}. Delegate to the appropriate specialists, reconcile their evidence, and make a safe recommendation. Do not execute payments or contact anyone.", data)

def _event_text(value: Any, limit: int = 500) -> str:
    if isinstance(value, str):
        return " ".join(value.split())[:limit]
    return str(_event_value(value))[:limit]

def _event_value(value: Any):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _event_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_event_value(item) for item in value]
    if hasattr(value, "model_dump"):
        return _event_value(value.model_dump(mode="json"))
    return str(value)[:4000]
