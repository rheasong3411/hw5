import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import type {
  Approval,
  Payment,
  Run,
  ShopEvent,
  Ticket,
  TicketSummary,
  HumanDecision,
} from "../types";
export function useShopData() {
  const [tickets, setTickets] = useState<Ticket[]>([]),
    [selectedId, setSelectedId] = useState(101),
    [run, setRun] = useState<Run | null>(null),
    [events, setEvents] = useState<ShopEvent[]>([]),
    [approvals, setApprovals] = useState<Approval[]>([]),
    [decisions, setDecisions] = useState<HumanDecision[]>([]),
    [requests, setRequests] = useState<Approval[]>([]),
    [payments, setPayments] = useState<Payment[]>([]),
    [balance, setBalance] = useState(0),
    [shopDate, setShopDate] = useState(""),
    [summary, setSummary] = useState<TicketSummary | null>(null),
    [error, setError] = useState(""),
    [balanceFlash, setBalanceFlash] = useState(false);
  const lastBalance = useRef(0);
  const refresh = useCallback(async () => {
    try {
      const [t, a, b, r, p, d] = await Promise.all([
        api.tickets(),
        api.approvals(),
        api.balance(),
        api.requests(),
        api.payments(),
        api.decisions(),
      ]);
      setTickets(t);
      setApprovals(a);
      setRequests(r);
      setPayments(p);
      setDecisions(d);
      lastBalance.current ||= b.balance;
      setBalance(b.balance);
      setShopDate(b.date);
    } catch (e) {
      setError(String(e));
    }
  }, []);
  useEffect(() => {
    refresh();
    const timer = window.setInterval(() => {
      if (!run || ["completed", "stopped", "error"].includes(run.status))
        refresh();
    }, 10000);
    return () => window.clearInterval(timer);
  }, [refresh, run]);
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setRun(null);
        setEvents([]);
        setSummary(null);
        const runs = await api.runs();
        const latest = runs.find((item) => item.ticket_id === selectedId);
        if (!latest || cancelled) return;
        setRun(latest);
        const events = await api.events(latest.run_id);
        if (cancelled) return;
        setEvents(events);
        if (
          latest.status === "completed" ||
          latest.status === "stopped" ||
          latest.status === "error"
        )
          setSummary(await api.summary(selectedId, latest.run_id));
      } catch (e) {
        if (!cancelled) setError(String(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedId]);
  useEffect(() => {
    if (!run || ["completed", "stopped", "error"].includes(run.status)) return;
    const timer = window.setInterval(async () => {
      try {
        const [r, e, a, b, allRequests, allPayments, allDecisions] = await Promise.all([
          api.runStatus(run.run_id),
          api.events(run.run_id),
          api.approvals(),
          api.balance(),
          api.requests(),
          api.payments(),
          api.decisions(),
        ]);
        setRun(r);
        setEvents(e);
        setApprovals(a);
        setRequests(allRequests);
        setPayments(allPayments);
        setDecisions(allDecisions);
        if (b.balance !== lastBalance.current) {
          setBalanceFlash(true);
          window.setTimeout(() => setBalanceFlash(false), 1200);
          lastBalance.current = b.balance;
          setBalance(b.balance);
          setShopDate(b.date);
        }
        if (["completed", "stopped", "error"].includes(r.status)) {
          const [t, s] = await Promise.all([
            api.tickets(),
            api.summary(selectedId, run.run_id),
          ]);
          setTickets(t);
          setSummary(s);
        }
      } catch (e) {
        setError(String(e));
      }
    }, 1200);
    return () => window.clearInterval(timer);
  }, [run, selectedId]);
  const select = (id: number) => {
    if (id === selectedId) return;
    setSelectedId(id);
    setSummary(null);
  };
  const start = async () => {
    try {
      setError("");
      setEvents([]);
      setSummary(null);
      setRun(await api.run(selectedId));
    } catch (e) {
      setError(String(e));
    }
  };
  return {
    tickets,
    selectedId,
    selected: tickets.find((t) => t.id === selectedId),
    run,
    events,
    approvals,
    decisions,
    requests,
    payments,
    balance,
    shopDate,
    summary,
    error,
    balanceFlash,
    select,
    start,
    refresh,
    setError,
  };
}
