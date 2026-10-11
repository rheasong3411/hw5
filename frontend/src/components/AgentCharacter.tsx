import type { Role } from "../types";
export function AgentCharacter({ role }: { role: Role }) {
  const colors: Record<Role, string> = {
    boss: "#bd804a",
    inventory: "#5e87a7",
    accounting: "#bf9b52",
    facilities: "#8d6f61",
    customer_service: "#7299a6",
  };
  return (
    <svg className="character" viewBox="0 0 70 105" aria-hidden="true">
      <circle cx="35" cy="19" r="15" fill="#e5b48a" />
      <path d="M19 18Q35 0 51 18" fill={colors[role]} />
      <path d="M13 102Q14 52 35 49Q56 52 57 102" fill={colors[role]} />
      {role === "boss" && <path d="M31 48h8l3 36h-14z" fill="#17334f" />}
      {role === "inventory" && (
        <path
          d="M20 51h30v47H20zM20 58h30"
          fill="#d8b58a"
          stroke="#17334f"
          strokeWidth="2"
        />
      )}
      {role === "accounting" && <path d="M18 47h34v9H18z" fill="#5e836b" />}
      {role === "facilities" && (
        <path
          d="M42 55q12 8 5 38M47 88l7 5m-7-5l-7 5"
          fill="none"
          stroke="#d49a3a"
          strokeWidth="3"
        />
      )}
      {role === "customer_service" && (
        <path
          d="M50 18q13 2 7 15M54 30h-7"
          fill="none"
          stroke="#17334f"
          strokeWidth="3"
        />
      )}
      <circle cx="29" cy="20" r="2" fill="#17334f" />
      <circle cx="41" cy="20" r="2" fill="#17334f" />
      <path d="M29 29q6 5 12 0" stroke="#7f493b" fill="none" strokeWidth="2" />
    </svg>
  );
}
