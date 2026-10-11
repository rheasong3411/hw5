import type { ShopEvent } from "../types";
import { ROLE_NAMES } from "../types";
export function DelegationNote({ event }: { event: ShopEvent }) {
  return (
    <div className="delegation-note">
      ✦ {ROLE_NAMES[event.from_agent || event.agent] || event.agent} →{" "}
      {ROLE_NAMES[event.to_agent || ""] || event.to_agent}
    </div>
  );
}
