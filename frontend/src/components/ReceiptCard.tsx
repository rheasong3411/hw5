import type { Approval } from "../types";
export function ReceiptCard({
  approval,
  approver,
  onApprove,
  onReject,
}: {
  approval: Approval;
  approver: string;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <article className="receipt-card">
      <div className="receipt-top">
        <span>✦ CAMPUS CUSTOMS</span>
        <small>PENDING SIGNATURE</small>
      </div>
      <div className="receipt-line">
        <span>{approval.kind.replaceAll("_", " ").toUpperCase()}</span>
        <strong>{formatMoney(approval.amount)}</strong>
      </div>
      <p>Reference: {approval.ref_id ?? "vendor order"}</p>
      {approval.expected_arrival && (
        <p>Expected arrival: {approval.expected_arrival}</p>
      )}
      <div className="receipt-actions">
        <button
          onClick={onApprove}
          aria-label={`Approve ${approval.kind} for ${approver}`}
        >
          Approve
        </button>
        <button className="reject-button" onClick={onReject}>
          Reject
        </button>
      </div>
    </article>
  );
}

function formatMoney(amount: number) {
  return `$${amount.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}
