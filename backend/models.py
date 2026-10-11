"""Typed contracts shared by the five agents and the review/audit layer."""
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

AgentRole = Literal["boss", "inventory", "accounting", "facilities", "customer_service", "system"]

class Ticket(BaseModel):
    id: int
    type: str
    requester: str
    subject: str
    status: str
    notes: str | None = None
    sku: str | None = None
    size: str | None = None
    qty: int | None = None
    lease_id: int | None = None
    invoice_id: int | None = None

class Delegation(BaseModel):
    from_agent: AgentRole
    to_agent: AgentRole
    ticket_id: int
    task: str = Field(min_length=1)

class AuditEvent(BaseModel):
    timestamp: datetime
    run_id: str
    step: int
    agent: AgentRole
    action: str
    ticket_id: int | None = None
    detail: dict[str, Any] = Field(default_factory=dict)
    outcome: str = "completed"
