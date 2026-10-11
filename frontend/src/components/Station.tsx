import type { Role, ShopEvent } from "../types";
import { ROLE_NAMES } from "../types";
import { AgentCharacter } from "./AgentCharacter";
import { SpeechBubble } from "./SpeechBubble";
const props: Record<Role, { action: string }> = {
  boss: { action: "clipboard desk" },
  inventory: { action: "folded hoodies + boxes" },
  accounting: { action: "calculator + receipts" },
  facilities: { action: "keys + lease papers" },
  customer_service: { action: "open laptop counter" },
};
function StationProp({ role }: { role: Role }) {
  if (role === "inventory")
    return (
      <svg className="drawn-prop shelves" viewBox="0 0 90 52">
        <path
          d="M4 4h82v44H4zM4 18h82M4 33h82"
          fill="#d8b384"
          stroke="#17334f"
          strokeWidth="2"
        />
        <path
          d="M12 9h20l4 6H9zM48 9h20l4 6H45zM12 24h20l4 6H9zM48 24h20l4 6H45z"
          fill="#17334f"
        />
        <path d="M9 38h28v8H9zM51 38h28v8H51z" fill="#f6e6ca" />
      </svg>
    );
  if (role === "accounting")
    return (
      <svg className="drawn-prop calculator" viewBox="0 0 90 52">
        <rect
          x="7"
          y="4"
          width="31"
          height="43"
          rx="3"
          fill="#f8f1e5"
          stroke="#17334f"
          strokeWidth="2"
        />
        <rect x="13" y="10" width="19" height="10" fill="#f8f1e5" />
        <path
          d="M14 27h4m5 0h4m-13 8h4m5 0h4m-13 8h4m5 0h4"
          stroke="#17334f"
          strokeWidth="3"
        />
        <path
          d="M50 8h27v36H50zM56 16h15M56 23h15M56 30h10"
          fill="#fffaf0"
          stroke="#17334f"
          strokeWidth="2"
        />
      </svg>
    );
  if (role === "facilities")
    return (
      <svg className="drawn-prop facilities-prop" viewBox="0 0 90 52">
        <rect
          x="5"
          y="4"
          width="55"
          height="42"
          rx="2"
          fill="#a66d4e"
          stroke="#17334f"
          strokeWidth="2"
        />
        <path
          d="M13 15h28M13 22h20M13 29h32"
          stroke="#17334f"
          strokeWidth="3"
        />
        <path
          d="M70 15q10 4 0 9q-10 5 0 10M69 15v24"
          fill="none"
          stroke="#d49a3a"
          strokeWidth="3"
        />
        <path d="M49 8v10h9" fill="#f8f1e5" stroke="#9d6849" />
      </svg>
    );
  if (role === "customer_service")
    return (
      <svg className="drawn-prop laptop" viewBox="0 0 90 52">
        <path
          d="M20 6h50v30H20z"
          fill="#f8f1e5"
          stroke="#17334f"
          strokeWidth="3"
        />
        <path
          d="M10 41h70l-7 6H17z"
          fill="#7093aa"
          stroke="#17334f"
          strokeWidth="3"
        />
        <path d="M28 15h34v12H28z" fill="#d8e4e8" />
      </svg>
    );
  return (
    <svg className="drawn-prop clipboard" viewBox="0 0 90 52">
      <path
        d="M24 8h43v39H24z"
        fill="#f8f1e5"
        stroke="#9d6849"
        strokeWidth="3"
      />
      <path
        d="M35 8V3h21v5M32 20h25M32 29h25M32 38h16"
        fill="none"
        stroke="#17334f"
        strokeWidth="3"
      />
    </svg>
  );
}
export function Station({
  role,
  events,
  active,
}: {
  role: Role;
  events: ShopEvent[];
  active: boolean;
}) {
  const mine = events.filter((e) => e.agent === role),
    last = mine[mine.length - 1],
    working = !!last && !["final_output", "token_usage"].includes(last.action),
    delegating = mine.some((e) => e.action === "delegation_requested"),
    status = !last
      ? "Idle"
      : delegating && working
        ? "Delegating"
        : working
          ? "Working"
          : "Done";
  return (
    <article
      className={`station station-${role} ${working ? "is-working" : ""}`}
    >
      <StationProp role={role} />
      <AgentCharacter role={role} />
      <div className="station-top" />
      <div className="station-front" />
      <div className="station-label">
        <h3>{ROLE_NAMES[role]}</h3>
        <span className={`status-chip status-${status.toLowerCase()}`}>
          {status}
        </span>
        <small>{props[role].action}</small>
      </div>
      {active && working && last && <SpeechBubble text={bubbleText(last)} />}
    </article>
  );
}

function bubbleText(event: ShopEvent) {
  const clean = (value: unknown) =>
    String(value ?? "")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 60);
  if (event.action === "delegation_requested")
    return `Asking ${ROLE_NAMES[event.to_agent || ""] || event.to_agent}: ${clean(event.task)}`;
  if (event.action === "tool_call")
    return `Checking ${event.tool || "a shop record"}`;
  if (event.action === "loop_start")
    return `Starting: ${clean(event.task || event.text)}`;
  if (event.action === "model_response" || event.action === "final_output")
    return clean(event.text);
  return clean(event.text || event.tool || "Working through the ticket");
}
