import asyncio


def test_nested_mock_delegations_share_one_six_success_budget():
    import backend.agents as agents

    async def mock_run_agent(role, task, child):
        next_role = {
            "inventory": "accounting",
            "accounting": "facilities",
            "facilities": "customer_service",
            "customer_service": "inventory",
        }.get(role, "customer_service")
        if child.depth < agents.MAX_DELEGATION_DEPTH:
            await agents.delegate_with_budget(
                child, role, next_role, f"nested:{task}", mock_run_agent
            )
        else:
            await agents.delegate_with_budget(
                child, role, next_role, f"depth:{task}", mock_run_agent
            )
        return f"mock answer from {role}"

    async def scenario():
        data = agents.RunContextData("budget-test", 103)
        roots = ["inventory", "accounting", "facilities", "customer_service"] * 3
        await asyncio.gather(
            *(
                agents.delegate_with_budget(data, "boss", role, f"root task {index}", mock_run_agent)
                for index, role in enumerate(roots)
            )
        )
        assert data.budget.delegation_attempts > data.budget.delegation_successes
        assert data.budget.delegation_successes == agents.MAX_DELEGATIONS_PER_RUN
        assert data.budget.delegation_successes <= 6

    asyncio.run(scenario())
