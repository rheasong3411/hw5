export function BalanceCard({
  balance,
  flash,
}: {
  balance: number;
  flash: boolean;
}) {
  return (
    <section className={`balance-card ${flash ? "balance-flash" : ""}`}>
      <span>CHECKING BALANCE</span>
      <strong>
        ${balance.toLocaleString("en-US", { minimumFractionDigits: 2 })}
      </strong>
      <small>Available for shop operations</small>
    </section>
  );
}
