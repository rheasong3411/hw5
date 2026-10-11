import type { Approval, Ticket } from "../types";
function money(value: number) {
  return `$${value.toLocaleString("en-US", { minimumFractionDigits: 2 })}`;
}
export function TicketBoard({
  tickets,
  selectedId,
  onSelect,
  requests,
  decisions,
}: {
  tickets: Ticket[];
  selectedId: number;
  onSelect: (id: number) => void;
  requests: Approval[];
  decisions: import("../types").HumanDecision[];
}) {
  return (
    <aside className="ticket-board">
      <div className="board-pin" />
      <h2>Ticket board</h2>
      <p className="board-subtitle">Campus shop queue</p>
      {tickets.map((ticket) => (
        <button
          className={`ticket-card ${ticket.id === selectedId ? "selected" : ""}`}
          key={ticket.id}
          onClick={() => {
            if (ticket.id !== selectedId) onSelect(ticket.id);
          }}
        >
          <span className="ticket-tag">#{ticket.id}</span>
          <span className="ticket-copy">
            <strong>{ticket.subject}</strong>
            <small>{ticket.requester}</small>
            <small>{ticket.type.replaceAll("_", " ")}</small>
          </span>
          {ticket.status === "resolved" && (
            <span className="resolved-stamp">RESOLVED</span>
          )}
          {ticket.status === "awaiting_approval" && (
            <span className="awaiting-stamp awaiting-approval-stamp">AWAITING APPROVAL</span>
          )}
          {ticket.status === "awaiting_decision" && <span className="awaiting-stamp awaiting-decision-stamp">AWAITING DECISION</span>}
          <span className="request-chip">
            {requests.filter((r) => r.ticket_id === ticket.id).length
              ? requests
                  .filter((r) => r.ticket_id === ticket.id)
                  .map(
                    (r) =>
                      `${r.status === "used" ? "PAID" : r.status.toUpperCase()}${r.kind === "purchase_order" ? " PO" : ""} · ${money(r.amount)} · ${r.approved_by || r.rejected_by || "pending"}`,
                  )
                  .join(" · ")
              : decisions.filter((d) => d.ticket_id === ticket.id && d.status === "pending").length
                ? `${decisions.filter((d) => d.ticket_id === ticket.id && d.status === "pending").length} decision pending`
                : "No requests"}
          </span>
        </button>
      ))}
      <div className="board-note">
        Choose a card to send the team to its station.
      </div>
    </aside>
  );
}
