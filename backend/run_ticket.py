"""Run exactly one ticket through the Luna agent team."""
import asyncio
import sys
from .agents import run_ticket

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: .venv/bin/python -m backend.run_ticket TICKET_ID")
    print(asyncio.run(run_ticket(int(sys.argv[1]))))
