import { useState } from "react";
import type { SummaryAgent, TicketSummary } from "../types";
import { ROLE_NAMES } from "../types";

function SummaryAgentCard({ agent }: { agent: SummaryAgent }) {
  const [expanded, setExpanded] = useState(false);
  const clean = agent.summary
    .replace(/```[\s\S]*?```/g, "")
    .replace(/\*\*|__/g, "")
    .replace(/`/g, "")
    .replace(/^\s*#+\s?/gm, "")
    .replace(/\s+/g, " ")
    .trim();
  const short = clean.slice(0, 260);
  return (
    <article>
      <b>{ROLE_NAMES[agent.agent] || agent.agent}</b>
      <p>
        {expanded ? clean : short}
        {clean.length > short.length && !expanded ? "…" : ""}
      </p>
      {clean.length > short.length && (
        <button className="more-button" onClick={() => setExpanded(!expanded)}>
          {expanded ? "less" : "more"}
        </button>
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
