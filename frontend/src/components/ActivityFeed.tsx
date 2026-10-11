import { useEffect, useRef, useState } from "react";
import type { ShopEvent } from "../types";
import { ROLE_NAMES } from "../types";

function clean(value: unknown, limit = 200) {
  return String(value ?? "")
    .replace(/```[\s\S]*?```/g, "")
    .replace(/\*\*|__/g, "")
    .replace(/`/g, "")
    .replace(/^\s*#+\s?/gm, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, limit);
}

function argsText(args: unknown) {
  if (!args || typeof args !== "object") return "";
  return Object.entries(args as Record<string, unknown>)
    .filter(([key]) => key !== "ctx")
    .map(([key, value]) => `${key} ${clean(value, 50)}`)
    .join(" · ");
}

function eventText(event: ShopEvent) {
  if (event.action === "delegation_requested") {
    return `→ ${ROLE_NAMES[event.to_agent || ""] || event.to_agent}: ${clean(event.task)}`;
  }
  if (event.action === "tool_call") {
    return `${event.tool || "tool"}${argsText(event.args) ? ` · ${argsText(event.args)}` : ""}`;
  }
  if (event.action === "loop_start") return clean(event.task || event.text);
  if (event.action === "tool_result")
    return clean(event.text || "Tool returned database evidence.");
  if (event.action === "model_request") return "";
  return clean(event.text || event.tool || event.action.replaceAll("_", " "));
}
export function ActivityFeed({
  events,
  error,
}: {
  events: ShopEvent[];
  error: string;
}) {
  const end = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState("all");
  const [compact, setCompact] = useState(false);
  useEffect(() => {
    end.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [events.length]);
  return (
    <section className="activity-feed">
      <div className="section-heading">
        <h2>Activity feed</h2>
        <div className="feed-controls">
          <span>
            {events.length
              ? `${events.length} live events`
              : "Waiting for a run"}
          </span>
          <button onClick={() => setCompact(!compact)}>
            {compact ? "Expand" : "Compact"}
          </button>
        </div>
      </div>
      <div className="filter-chips">
        {[
          ["all", "All"],
          ["boss", "Boss"],
          ["inventory", "Inventory"],
          ["accounting", "Accounting"],
          ["facilities", "Facilities"],
          ["customer_service", "Customer Service"],
        ].map(([value, label]) => (
          <button
            className={filter === value ? "active" : ""}
            key={value}
            onClick={() => setFilter(value)}
          >
            {label}
          </button>
        ))}
      </div>
      {error && <div className="inline-error">{error}</div>}
      {events.filter((event) => event.action !== "model_request").length ? (
        events
          .filter((event) => filter === "all" || event.agent === filter)
          .filter((event) => event.action !== "model_request")
          .map((event) => (
            <div
              className={`activity-row ${compact ? "compact" : ""}`}
              key={event.id}
            >
              <span className={`agent-dot dot-${event.agent}`}>
                {(ROLE_NAMES[event.agent] || event.agent).charAt(0)}
              </span>
              <div>
                <b>{ROLE_NAMES[event.agent] || event.agent}</b>
                <span className="event-action">
                  {event.action.replaceAll("_", " ")}
                  {event.tool ? ` · ${event.tool}` : ""}
                </span>
                <p>{eventText(event)}</p>
              </div>
            </div>
          ))
      ) : (
        <p className="empty-state">
          Start a ticket to see real agent events arrive here.
        </p>
      )}
      <div ref={end} />
    </section>
  );
}
