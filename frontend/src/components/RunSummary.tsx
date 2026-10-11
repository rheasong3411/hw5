import { useState } from "react";
import type { SummaryAgent, TicketSummary } from "../types";
import { ROLE_NAMES } from "../types";

function SummaryAgentCard({ agent }: { agent: SummaryAgent }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <article>
      <b>{ROLE_NAMES[agent.agent] || agent.agent}</b>
      {agent.run_end_status && (
        <small className="run-end-status">
          {ROLE_NAMES[agent.agent] || agent.agent} status at run end:{" "}
          {agent.run_end_status}
        </small>
      )}
      <p>{agent.outcome}</p>
      <button className="more-button" onClick={() => setExpanded(!expanded)}>
        {expanded ? "Hide full answer" : "Show full answer"}
      </button>
      {expanded && (
        <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
          {agent.full_answer}
        </pre>
      )}
      <small>
        Tools: {agent.tools.length ? agent.tools.join(", ") : "none"}
        {agent.delegated_to.length
          ? ` · Delegated to ${agent.delegated_to.join(", ")}`
          : ""}
      </small>
    </article>
  );
}
export function RunSummary({ summary }: { summary: TicketSummary | null }) {
  if (!summary) return null;
  return (
    <section className="run-summary">
      <div className="section-heading">
        <h2>Run summary</h2>
        <span>Latest completed run</span>
      </div>
      {summary.disposition && (
        <article className="disposition">
          <b>Disposition · {summary.disposition.final_status}</b>
          {summary.disposition.requests.map((r) => (
            <p key={r.id}>
              Request {r.id} · {r.kind} · ${Number(r.amount || 0).toFixed(2)} ·{" "}
              {r.status}
              {r.decided_by ? ` by ${r.decided_by}` : ""}
            </p>
          ))}
          {summary.disposition.decisions.map((d) => (
            <p key={d.id}>
              Decision {d.id} · {d.kind} · {d.choice || "pending"}
              {d.terms ? `: ${d.terms}` : ""}
              {d.decided_by ? ` · by ${d.decided_by}` : ""}
              {d.decided_at ? ` · ${d.decided_at}` : ""}
            </p>
          ))}
          {summary.disposition.remaining_actions.map((x) => (
            <p key={x}>Remaining: {x}</p>
          ))}
        </article>
      )}
      <p className="run-metrics">
        Delegations: {summary.delegation_successes ?? 0} successful /{" "}
        {summary.delegation_attempts ?? 0} attempts
        {summary.returned_models?.length
          ? ` · Models: ${summary.returned_models.map((model) => model.model_name).join(", ")}`
          : ""}
      </p>
      {summary.agents.map((agent) => (
        <SummaryAgentCard key={agent.agent} agent={agent} />
      ))}
    </section>
  );
}
