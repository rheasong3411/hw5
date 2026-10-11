import React from "react";
import type { Approval, HumanDecision, Payment } from "../types";
import { ReceiptCard } from "./ReceiptCard";
export function ManagerDesk({
  approvals,
  requests,
  payments,
  balance,
  approver,
  onApproverChange,
  onApprove,
  onReject,
  decisions,
  onDecide,
}: {
  approvals: Approval[];
  requests: Approval[];
  payments: Payment[];
  balance: number;
  approver: string;
  onApproverChange: (name: string) => void;
  onApprove: (a: Approval) => void;
  onReject: (a: Approval) => void;
  decisions: HumanDecision[];
  onDecide: (d: HumanDecision, choice: string, terms: string) => void;
}) {
  const historical = requests.filter((request) => request.status !== "pending");
  const start =
    payments.reduce((sum, payment) => sum + payment.amount, 0) + balance;
  return (
    <aside className="manager-desk">
      <div className="desk-label">MANAGER'S DESK</div>
      <label className="approver-field">
        Signed in as{" "}
        <input
          value={approver}
          onChange={(e) => onApproverChange(e.target.value)}
        />
      </label>
      <section className="approval-panel">
        <h2>Approval requests</h2>
        {approvals.length ? (
          approvals.map((a) => (
            <ReceiptCard
              key={a.request_id}
              approval={a}
              approver={approver}
              onApprove={() => onApprove(a)}
              onReject={() => onReject(a)}
            />
          ))
        ) : (
          <p className="empty-state">No receipts waiting for your signature.</p>
        )}
      </section>
      <section className="approval-panel">
        <h2>Human decisions</h2>
        {decisions.filter((d) => d.status === "pending").map((d) => (
          <DecisionCard key={d.decision_id} decision={d} onDecide={onDecide} />
        ))}
        {!decisions.some((d) => d.status === "pending") && <p className="empty-state">No decisions waiting for your signature.</p>}
      </section>
      <section className="payments-ledger">
        <h3>Payments ledger</h3>
        {payments.length ? (
          payments.map((payment) => (
            <div className="ledger-row" key={payment.id}>
              <span>
                #{payment.id} · {payment.kind}
              </span>
              <span>
                {payment.ref_id} · $
                {payment.amount.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                })}{" "}
                · {payment.approved_by}
              </span>
            </div>
          ))
        ) : (
          <p className="empty-state">No payments recorded.</p>
        )}
        <strong>
          Start ${start.toLocaleString("en-US", { minimumFractionDigits: 2 })} →
          now ${balance.toLocaleString("en-US", { minimumFractionDigits: 2 })}
        </strong>
      </section>
      <details className="decision-history">
        <summary>Decision history</summary>
        {historical.length ? (
          historical.map((request) => (
            <div className="history-receipt" key={request.request_id}>
              <b
                className={
                  request.status === "used" ? "paid-ink" : "rejected-ink"
                }
              >
                {request.status === "used" ? "PAID" : "REJECTED"}
              </b>
              <span>
                {request.kind.replaceAll("_", " ")} · $
                {request.amount.toLocaleString("en-US", {
                  minimumFractionDigits: 2,
                })}
              </span>
              <small>{request.approved_by || request.rejected_by}</small>
            </div>
          ))
        ) : (
          <p className="empty-state">No payment decisions yet.</p>
        )}
        {decisions.filter((d) => d.status === "decided").map((d) => <div className="history-receipt" key={d.decision_id}><b>DECIDED</b><span>{d.choice}</span><small>{d.decided_by} · {d.decided_at ? new Date(d.decided_at).toLocaleString() : ""}</small><small>{d.terms}</small></div>)}
      </details>
    </aside>
  );
}

function DecisionCard({ decision, onDecide }: { decision: HumanDecision; onDecide: (d: HumanDecision, choice: string, terms: string) => void }) {
  const [terms, setTerms] = React.useState(decision.recommendation);
  return <article className="receipt-card"><h3>{decision.question}</h3><p>{decision.recommendation}</p><textarea aria-label="Decision terms" value={terms} onChange={(e) => setTerms(e.target.value)} />{decision.options.map((option) => <button key={option} onClick={() => onDecide(decision, option, terms)}>{option}</button>)}<button onClick={() => onDecide(decision, "custom", terms)}>Custom decision</button></article>;
}
