import type { Role, ShopEvent } from "../types";
import { ROLES } from "../types";
import { Station } from "./Station";
import { DelegationNote } from "./DelegationNote";
export function ShopScene({
  events,
  active,
}: {
  events: ShopEvent[];
  active: boolean;
}) {
  const delegations = active
    ? events.filter((e) => e.action === "delegation_requested" && e.to_agent)
    : [];
  return (
    <div className="scene-wrap">
      <div className="scene">
        <div className="back-wall">
          <svg
            className="campus-pennant"
            viewBox="0 0 76 68"
            aria-label="Original Yale-inspired pennant"
          >
            <path
              d="M4 5h68L38 57z"
              fill="var(--navy)"
              stroke="var(--navy)"
              strokeWidth="2"
            />
            <text
              x="38"
              y="40"
              textAnchor="middle"
              fill="#fffaf0"
              fontFamily="Georgia, serif"
              fontSize="30"
              fontWeight="bold"
            >
              Y
            </text>
            <path d="M8 60h60l-10 7H18z" fill="#d49a3a" />
            <text
              x="38"
              y="65"
              textAnchor="middle"
              fill="var(--navy)"
              fontFamily="Georgia, serif"
              fontSize="5"
              fontWeight="bold"
            >
              BULLDOGS
            </text>
          </svg>
          <svg
            className="campus-window"
            viewBox="0 0 86 112"
            aria-label="Gothic pointed arch window"
          >
            <path
              d="M8 108V45Q43 2 78 45v63z"
              fill="#d8d0c0"
              stroke="#17334f"
              strokeWidth="3"
            />
            <path
              d="M43 20v88M16 61h54M25 42l18 19 18-19M25 84l18-23 18 23"
              fill="none"
              stroke="#8b98a0"
              strokeWidth="2"
            />
            <path d="M17 105h52" stroke="#f8f1e5" strokeWidth="5" />
          </svg>
          <svg
            className="elm-garland"
            viewBox="0 0 88 34"
            aria-label="Elm leaves"
          >
            <path
              d="M4 25Q35 4 84 17"
              fill="none"
              stroke="#5e836b"
              strokeWidth="2"
            />
            <path
              d="M18 19q-10-12-13 2q8 7 13-2M36 12q-8-12-13 1q7 8 13-1M58 11q-7-11-13 2q7 7 13-2M78 15q-5-10-12-1q5 8 12 1"
              fill="#6e8b6c"
              stroke="#17334f"
              strokeWidth="1"
            />
          </svg>
          <div className="shop-sign">
            CAMPUS CUSTOMS <small>MERCH · SERVICE · CARE</small>
          </div>
          <svg
            className="pennant-row"
            viewBox="0 0 280 40"
            aria-label="Campus pennants"
          >
            <path d="M4 4h272" stroke="#9d6849" strokeWidth="2" />
            <path
              d="M18 4v28L31 20L44 32V4M67 4v28L80 20L93 32V4M116 4v28L129 20L142 32V4M165 4v28L178 20L191 32V4M214 4v28L227 20L240 32V4"
              fill="#d49a3a"
            />
          </svg>
          <div className="tote-bag">CC</div>
          <div className="wall-clock">10:30</div>
          <div className="wall-shelf">
            <i />
            <i />
            <i />
          </div>
          <div className="plant" aria-label="potted plant">
            <span className="plant-leaf leaf-one" />
            <span className="plant-leaf leaf-two" />
            <span className="plant-pot" />
          </div>
        </div>
        <div className="floorboards" />
        <div className="boss-rug" />
        <svg
          className="bulldog"
          viewBox="0 0 120 80"
          aria-label="Original side-profile English bulldog facing left"
        >
          <ellipse
            cx="68"
            cy="48"
            rx="34"
            ry="18"
            fill="#d9a066"
            stroke="#00356B"
            strokeWidth="1.5"
          />
          <ellipse cx="44" cy="52" rx="10" ry="12" fill="#fff8ec" />
          <rect x="38" y="58" width="9" height="16" rx="4" fill="#d9a066" />
          <rect x="52" y="58" width="9" height="16" rx="4" fill="#d9a066" />
          <rect x="78" y="58" width="9" height="16" rx="4" fill="#d9a066" />
          <rect x="92" y="58" width="9" height="16" rx="4" fill="#d9a066" />
          <ellipse cx="42.5" cy="74" rx="5" ry="2.5" fill="#fff8ec" />
          <ellipse cx="56.5" cy="74" rx="5" ry="2.5" fill="#fff8ec" />
          <ellipse cx="82.5" cy="74" rx="5" ry="2.5" fill="#fff8ec" />
          <ellipse cx="96.5" cy="74" rx="5" ry="2.5" fill="#fff8ec" />
          <path
            d="M101 40q14-8 13 3q-2 7-11 6"
            fill="none"
            stroke="#00356B"
            strokeWidth="2"
            strokeLinecap="round"
            className="bulldog-tail"
          />
          <rect
            x="8"
            y="22"
            width="36"
            height="32"
            rx="12"
            fill="#d9a066"
            stroke="#00356B"
            strokeWidth="1.5"
          />
          <rect
            x="4"
            y="36"
            width="18"
            height="16"
            rx="6"
            fill="#f1c48a"
            stroke="#00356B"
            strokeWidth="1"
          />
          <ellipse cx="7" cy="38" rx="3.5" ry="3" fill="#00356B" />
          <path
            d="M7 50q8 9 17 2"
            fill="none"
            stroke="#9d6849"
            strokeWidth="2"
          />
          <path
            d="M9 51l3 4 3-4M15 51l3 4 3-4"
            fill="#fff8ec"
            stroke="#00356B"
            strokeWidth=".7"
          />
          <circle cx="24" cy="32" r="3" fill="#00356B" />
          <circle cx="23" cy="31" r=".8" fill="#fff8ec" />
          <path
            d="M18 27q7-5 14-1"
            fill="none"
            stroke="#9d6849"
            strokeWidth="1.5"
          />
          <path
            d="M8 34q6-4 12-2M10 37q5-3 10-1"
            fill="none"
            stroke="#9d6849"
            strokeWidth="1.2"
          />
          <path
            d="M34 22q8-9 12 1q-3 8-10 6z"
            fill="#b77d50"
            stroke="#00356B"
            strokeWidth="1.5"
          />
          <path
            d="M39 43q7 4 12 1v7q-7 3-12-1z"
            fill="var(--navy)"
            stroke="var(--navy)"
            strokeWidth="1.5"
          />
          <circle
            cx="48"
            cy="49"
            r="4"
            fill="#d49a3a"
            stroke="#00356B"
            strokeWidth="1"
          />
          <text
            x="48"
            y="51"
            textAnchor="middle"
            fill="#fff8ec"
            fontSize="4.5"
            fontFamily="Georgia, serif"
          >
            Y
          </text>
        </svg>
        <div className="stations">
          {ROLES.map((role: Role) => (
            <Station key={role} role={role} events={events} active={active} />
          ))}
        </div>
        {delegations.map((event) => (
          <DelegationNote key={event.id} event={event} />
        ))}
      </div>
      <div className="scene-caption">
        Live shop floor · status and speech updates come from the current
        backend run
      </div>
    </div>
  );
}
