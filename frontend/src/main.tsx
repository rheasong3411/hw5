import { createRoot } from "react-dom/client";
import { useState } from "react";
import "./styles.css";
import { useShopData } from "./hooks/useShopData";
import { api } from "./api";
import { TicketBoard } from "./components/TicketBoard";
import { ShopScene } from "./components/ShopScene";
import { ActivityFeed } from "./components/ActivityFeed";
import { ManagerDesk } from "./components/ManagerDesk";
import { BalanceCard } from "./components/BalanceCard";
import { RunSummary } from "./components/RunSummary";
function App() {
  const shop = useShopData();
  const [approver, setApprover] = useState("Manager");
  const ticket = shop.selected;
  const decide = async (
    approval: Parameters<typeof api.approve>[0],
    approved: boolean,
  ) => {
    try {
      shop.setError("");
      await (approved
        ? api.approve(approval, approver)
        : api.reject(approval, approver));
      await shop.refresh();
    } catch (e) {
      shop.setError(String(e));
    }
  };
  const runLabel = shop.run ? `Run ${shop.run.status}` : "No run yet";
  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <span className="brand-mark">CC</span>
          <div>
            <h1>Campus Customs</h1>
            <p>
              Agent operations desk · {shop.shopDate || "shop date loading…"}
              <small className="brand-tagline">
                Lux et Veritas · New Haven, CT
              </small>
            </p>
          </div>
        </div>
        <div className="header-status">
          <span className="live-light" /> Live backend desk ·{" "}
          {shop.run?.status === "running"
            ? `Running ticket ${shop.selectedId}`
            : shop.run
              ? shop.run.status
              : "Idle"}
        </div>
      </header>
      <div className="dashboard-grid">
        <TicketBoard
          tickets={shop.tickets}
          selectedId={shop.selectedId}
          onSelect={shop.select}
          requests={shop.requests}
          decisions={shop.decisions}
        />
        <section className="main-column">
          <div className="run-header">
            <div>
              <span className="eyebrow">SELECTED TICKET · {runLabel}</span>
              <h2>{ticket?.subject || "Loading tickets…"}</h2>
              <p>
                {ticket?.requester} · {ticket?.type.replaceAll("_", " ")}{" "}
                {shop.run?.status === "stopped" &&
                  "· Run stopped; ticket remains open."}
              </p>
            </div>
            <button
              className="start-button"
              onClick={shop.start}
              disabled={shop.run?.status === "running"}
            >
              {shop.run?.status === "running"
                ? "Team is working…"
                : "Start agent team"}
            </button>
          </div>
          <ShopScene
            events={shop.events}
            active={shop.run?.status === "running"}
          />
          <ActivityFeed events={shop.events} error={shop.error} />
        </section>
        <section className="right-column">
          <BalanceCard balance={shop.balance} flash={shop.balanceFlash} />
          <ManagerDesk
            approvals={shop.approvals}
            requests={shop.requests}
            decisions={shop.decisions}
            payments={shop.payments}
            balance={shop.balance}
            approver={approver}
            onApproverChange={setApprover}
            onApprove={(a) => decide(a, true)}
            onReject={(a) => decide(a, false)}
            onDecide={async (d, choice, terms) => { try { await api.decide(d, approver, choice, terms); await shop.refresh(); } catch (e) { shop.setError(String(e)); } }}
          />
          <RunSummary summary={shop.summary} />
        </section>
      </div>
    </main>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
