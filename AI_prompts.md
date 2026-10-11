# AI Prompts — Homework 5: Campus Customs Multi-Agent Operations

## Context (before problem work began)

> OK, so nothing needs to be worked on, but I'm just giving you the scenario: we are working on the Campus Customs multi-agent operations, which is the agentic team that runs the shop. Open tickets land on a board, including customer orders, rent, unpaid bills, discount requests, whatever the shop has to handle. We will build three pieces that talk to each other: an MCP server, a FastAPI backend with a multi-agent team, and a React dashboard so a human can watch the agents at work and approve requests.
>
> The agent team has full connectivity, so any agent may delegate tasks to any other agent for help. We will build the following agents:
> 1. Boss: reads each ticket, decides who should work on it, and makes final calls
> 2. Inventory: checks stock by SKU and size, spots shortfalls, and figures out which vendor can restock
> 3. Accounting: watches cash and invoices, checks margins, and prepares payments or purchase orders for human approval
> 4. Facilities: handles the shop space side (so leases, rent, etc.)
> 5. Customer service: drafts messages for customers
>
> The data is in data.zip in the folder. Unzip it so you have data/campus_customs.db; that file is the original shop database. Tables include desk, tickets, inventory, pricing, vendors, leases, cash_accounts, payments, and invoices.
>
> Our tools will update the database as tickets get resolved. Make a copy of the database file called data/campus_customs_new.db, and point the MCP server and backend at that working copy. Keep campus_customs.db untouched so we can reset when we want to restart resolving the tickets.
>
> For the rules of the shop:
> - The field desk.date_today is "today" for the shop; use this date to determine what is overdue
> - Vendor lead times come from the vendors table
> - A vendor will not ship new products while they still have an open unpaid invoice
> - Human approval is required for any payments. Points will be deducted if this is not done, so if a payment is made, make sure to update the relevant table
> - If there is not enough cash, the pay tool must refuse — there should be no negative balances
> - Cash only goes out in this homework — we did not model revenue, so no money comes in
> - Before a full run to resolve the tickets, make sure to reset the database to the original values
> - Do not email customers or call real vendors; drafts stay on the board
>
> In general, for this assignment, use the Portkey API key for AI calls. For this assignment, use only GPT 6 Luna through Portkey for every agent. Points will be deducted if any other model shows up in your code or runs.
>
> Work one problem at a time — the final submission will be a public GitHub repo.

## Problem 1: Vibe Coder Prompts

### Prompt(s) typed

> OK, so for problem 1: vibe coder prompts. First, create AI_prompts.md and keep it updated as we work as a log of what I typed to you. Put one section for each problem, and each section should include:
> 1. the problem number and title
> 2. at least one prompt I typed to you
> 3. one follow-up prompt if ever needed (if our first attempt didn't work), and one sentence on what was lacking after the first

### Follow-up prompt

No follow-up prompt was needed.

### What was lacking after the first attempt

Nothing was lacking after the first attempt.

## Problem 2: Study the Campus Customs Database

### Prompt(s) typed

> OK, problem 2: study the Campus Customs database. Open data/campus_customs.db and look through every single table and its fields. Copy the original file to data/campus_customs_new.db, which we will be updating for later problems. Study the three open tickets so we can see how they link to other tables. Then start output/harness.md: for each table, list the fields and one short line on why that table matters for the agents after. We will keep growing this harness file in later problems.

### Follow-up prompt

No follow-up prompt was needed.

### What was lacking after the first attempt

Nothing was lacking after the first attempt.

## Problem 3: Build the MCP Server

### Prompt(s) typed

> OK, problem 3: build the MCP server. First, write an MCP server in mcp_server/ using FastMCP. This MCP server will talk to data/campus_customs_new.db, and we do not need to connect or run it in this problem. Every agent in this homework uses the tools in this MCP server. We will add more tools to this later; for now, write three tools we know we will need for the tickets in the database (use your best judgement). Keep the names clear, and NEVER invent any data — only use the info in the database.
>
> In output/harness.md, list each of the three MCP tools. For every tool include:
> 1. which table it reads
> 2. which ticket it helps unlock (101, 102, or 103)
> 3. one sentence on why that tool is the right one for that ticket
>
> Vague lines like "read inventory" score low — tie the tool to the ticket (so be specific).
>
> Also add a short mcp_server/README.md file that explains what the MCP server is for, which database file it uses, and the three tools it has for now.

### Follow-up prompt

No follow-up prompt was needed.

### What was lacking after the first attempt

Nothing was lacking after the first attempt.

## Problem 4: Add the MCP Server to the Vibe Coder and Test Each Tool

### Prompt(s) typed

> OK, problem 4: add the MCP server to the vibe coder and test each tool. In the vibe coder (in our case Luna, right?), add the MCP server to this project so the vibe coder can call these tools. Save the connection JSON text in .mcp.json at the project root, or however we save the local MCP server lists. With the vibe coder connected, test each of the three MCP tools. Save the evidence of testing in output/mcp_smoke.json. For every tool, include:
> 1. the prompt you asked the vibe coder
> 2. the tool name
> 3. the tool output (must match values in data/campus_customs_new.db)

### Follow-up prompt

No follow-up prompt was needed.

### What was lacking after the first attempt

Nothing was lacking after the first attempt.

## Problem 5: Build the Agent Team and Grow the MCP Tools

### Prompt(s) typed

> OK, problem 5: build the agent team and grow the MCP tools.
>
> Build the agentic team for Campus Customs using PydanticAI: boss, inventory, accounting, facilities, and customer service. Give each agent a prompt, model configuration, and execution loop, and allow all agents to delegate tasks to one another.
>
> Put the agent prompts in backend/prompts/, and make sure it is one file per agent. Put data types in backend/models.py, and the agent files under backend/; your layout can vary as long as the five roles are clear. Use the Portkey API key and only Luna for every agent.
>
> Write detailed, role-specific prompts in your own words. Include the shop rules each agent needs, its responsibilities, and the boundaries of its work. Add any MCP tools the agents need to handle open tickets.
>
> All shop information must come through the MCP server connected to data/campus_customs_new.db. Do not create a separate shop-tool layer that bypasses MCP. Have the agents append records to output/audit_trail.json during execution. Log enough information about every agent-loop step to support later review, and preserve existing records between runs. Create output/harness.md documenting every agent and MCP tool, including newly added tools, and identify the database tables each tool uses. Include a short safety section covering safeguards for interactions involving real customers and money, plus limits on token usage. Update mcp_server/README.md so its tool list accurately reflects the completed implementation.

### Follow-up prompt

> The first attempt isn't complete: agents can't actually delegate to each other, any agent can fake a human approval and execute a payment, the prompts are too short, the audit trail only logs start/end, and find_restock_vendors never matches. Fix these: give every agent a delegate tool so any agent can hand work to any other; remove payment execution from the agents' MCP tools so only a human approval step outside the agents can pay; write detailed prompts for each role; log every step (tool calls, delegations, results, token usage) to output/audit_trail.json; make vendor lookup actually match products to vendors; add a token limit per run; and add a script to run one ticket so we can test it with Luna.

### What was lacking after the first attempt

The first implementation lacked real delegation, human-only payment execution, detailed prompts, complete auditing, working vendor matching, shared token limits, and a one-ticket test runner.

## Problem 6: Plan the Three Tickets

### Prompt(s) typed

> OK, problem 6: plan the three tickets.
>
> Write down what you expect the team to do on each open ticket before wiring the backend. Build output/desk_tickets.html, which is a page you can double-click, with one tab per ticket (101, 102, 103). Add empty Cash and Reflection tabs for later problems; leave them blank or with a short "coming later" note for now.
>
> On each ticket tab, fill in an Expected section only, and leave room for an Actual section you will fill in after you run the agents.
>
> For each ticket's Expected section, write:
> - who the Boss should call first and why
> - all the agent delegations you expect, not "Boss calls everyone"
> - which MCP tools you expect that run to use
>
> Note that plans that send every specialist on every ticket score low, so do not do that. Compare this plan to what actually happens when your agents resolve the three tickets.

### Follow-up prompt

No follow-up prompt was needed.

### What was lacking after the first attempt

Nothing was lacking after the first attempt.

## Problem 7: Backend Routes

### Prompt(s) typed

> OK, problem 7: backend routes.
>
> The React frontend dashboard (which we will be working on next problem) needs a backend it can call. In backend/main.py, use FastAPI and add routes that do the following:
> - return the three tickets and whether each is open or resolved
> - take a ticket id and run your agent team on that ticket
> - return recent agent events, so what each agent said and which tools they used, so the board can refresh
> - approve a payment or purchase after a human clicks approve, so agents only prepare the pay and this route is what actually changes cash
> - return the current checking balance from cash_accounts
> - reset the database to the original values when you want to try a fresh run
>
> From the backend/ folder, start the server with uvicorn main:app --reload --port 8000
>
> This turns on the backend at http://localhost:8000 so the frontend dashboard can call those routes.
>
> Then in output/harness.md, list each route in one line with what URL / what it does.

### Follow-up prompt

No follow-up prompt was needed.

### What was lacking after the first attempt

Nothing was lacking after the first attempt.

## Problem 8: Agent Dashboard

### Prompt(s) typed

> OK, problem 8: agent dashboard.
>
> In this problem, we are working on the frontend dashboard in frontend/ with React + Vite + TypeScript. The page should call the routes we built in problem 7, and at minimum the board should be able to do the following:
> - list all three tickets
> - let you pick one ticket and start the agent team on it
> - show each agent and what they are saying or doing while the ticket runs
> - mark a ticket resolved when the run finishes
> - show a short summary of what each agent did on that ticket
> - let a human approve a pay or purchase when asked
> - show the checking balance, which should drop after an approved pay
>
> Make the dashboard look good, be creative with the layout and feel, and treat this as a real desk people would want to sit at, so put thought into how it looks.
>
> (Make the dashboard feel like a miniature campus merchandise shop viewed from a slightly elevated angle. I want the setting to shape the interface, with thoughtful visual details and animated staff.
>
> Place an illustrated shop workspace in the center, with five recognizable stations:
> - Boss at a central desk with a clipboard.
> - Inventory beside shelves of folded sweatshirts and stock boxes.
> - Accounting at a desk with a calculator and receipts.
> - Facilities near a noticeboard with keys and lease documents.
> - Customer Service at the front counter with a laptop.
>
> Give each agent a consistent character, name label, and readable status. When an agent is working, gently highlight its station and show a short speech bubble with its latest action. When agents delegate, briefly animate a small task note moving between their stations. Keep full messages in a readable activity feed below the scene.
>
> Place the three tickets on a compact corkboard-style panel on the left. Use paper cards with clothing-tag ticket IDs. Make the selected ticket visually prominent, and give completed tickets a tasteful "Resolved" stamp.
>
> Put the checking balance and approval requests on the right as the manager's desk. Style requests like receipts, with clear amounts and Approve/Reject buttons. Keep the balance highly readable and briefly highlight it when a successful payment changes it.
>
> Use deep navy, warm cream, light wood tones, and muted blue, with amber for approvals. Include small campus shop details such as a pennant, hanging tote bag, folded hoodies, and a Campus Customs sign. Keep decoration subtle enough that messages and controls remain easy to read.
>
> Use crisp illustrations, gentle shadows, and restrained animation. Make the shop scene the focal point while keeping tickets, agent activity, approvals, summaries, and cash information accessible. All activity and status changes must reflect real backend events.)
>
> Tell the frontend to talk to the backend at http://localhost:8000, and on the backend, allow the Vite page origin, which usually should be http://localhost:5173, so the browser is allowed to call the routes. Start the board with:
> npm run dev
> This opens the React desk in the browser so you can pick the tickets and watch the agents.
>
> After implementing the dashboard, write output/design.md explaining the final design and why you chose it. Cover the layout, how the five agents are visually distinguished, how resolved tickets and the checking balance appear, and the creative details that make the campus shop setting engaging and practical. Describe only features actually implemented.

### Follow-up prompt

> The first attempt isn't done: styles.css is empty so the page shows unstyled default HTML, there is no illustrated shop scene, the agents are just text symbols, and design.md describes things that don't exist. Rebuild the dashboard properly: split it into readable components and a real stylesheet; draw the shop scene and the five stations and characters with SVG/CSS in the navy, cream, wood and muted-blue palette with amber approvals; add the corkboard tickets with clothing-tag IDs and a Resolved stamp, receipt-style approvals with Approve/Reject, speech bubbles, the delegation note animation, and the balance highlight, all driven by real backend events. Then check it in a browser and rewrite output/design.md to describe only what is actually built.

### What was lacking after the first attempt

The first attempt had an empty stylesheet, all the code in one compressed file, text symbols instead of an illustrated shop scene and characters, and a design.md that described features that did not exist.

### Second follow-up prompt

> I ran it in the browser and it still isn't right: agents keep delegating back and forth until they hit the token limit, a stopped run still gets marked resolved, the page is blank after a reload, the counters cover the agents' names, Boss isn't at a central desk, the props are still text symbols, and the code is all on one line. Fix these so the run finishes properly and the scene matches the design.

### What was lacking after the second attempt

The rebuilt dashboard looked right at first glance, but a live run exposed a delegation loop and a false "resolved" stamp, and the scene still didn't match the brief.

## Problem 9: Resolve the Tickets

### Prompt(s) typed

> OK, problem 9: resolve the tickets.
>
> Before we test the agents on a full run over the three tickets, reset the working database data/campus_customs_new.db again so we start clean. Note the starting checking balance after the reset, then run all three tickets (101, 102, 103) on the board until each is resolved. If a payment or purchase needs human approval, ask me through the board before proceeding.
>
> Then open output/desk_tickets.html from problem 6. On each ticket tab, fill in the "Actual" section based on the real run, including which agents worked on it, what they delegated and to whom, and which tools they used. Keep the "Expected" sections so we can compare the two.
>
> Then on the Cash tab of the same output/desk_tickets.html, itemize the money, including:
> - the starting checking balance after the reset
> - for each ticket, how cash changed during the run and why, including each payment or purchase and its dollar amount; if cash didn't change, explain why
> - the ending balance, which must match the checking balance in cash_accounts in the working database
>
> Wrong cash math will lose points even if the board shows every ticket resolved, so reconcile the starting balance, all actual cash outflows, and the ending balance. Don't count an approval or purchase order as cash leaving unless a payment actually happened.
>
> Also make sure we have:
> - output/resolved_tickets.json, with each ticket's id, final status, short outcome, what each agent contributed, and any human approvals
> - output/resolved_board.html, a page we can double-click to open, with a screenshot of the React board for each resolved ticket (101, 102, 103); make sure the screenshots display when opened locally
>
> Then append the real runs to output/audit_trail.json without overwriting the existing entries, and finish output/harness.md so it covers the tables, MCP tools, the five agents, API routes, the dashboard, and safety rules.
>
> Make sure everything reflects the actual runs and database results.

### Follow-up prompt

> These are the most important fixes, in order:
> 1. The payment tool can create negative cash when approvals happen simultaneously. Sequential payments work correctly, but in a separate test database I approved the $2,400 rent and the $264 hoodie PO concurrently after paying the invoice; both passed the cash check and checking became −$104. This directly violates the assignment's no-negative-balance rule. The balance check and debit need to happen atomically inside a locked transaction.
> 2. Tickets are marked resolved before the human decision. backend/main.py automatically resolves a ticket whenever the agent run finishes. All three final Boss responses actually say pending approval / keep the ticket open, but the backend overrides them. The audit confirms resolution happened before the invoice approval, rent approval, and PO rejection. Finishing the analysis and resolving the ticket need separate checks.
> 3. Agents can still close tickets through another tool. Although set_ticket_status is blocked from agents, they can call append_ticket_note(close_ticket=True). I reproduced this on a test copy. Remove that closing option from the agent-facing tool; otherwise the README and harness claims about this boundary are inaccurate.
> 4. The required model isn't established by the evidence. The prompt requires gpt-6-luna, but the configuration uses "luna". That might be a valid Portkey alias, but the submission doesn't prove its mapping, and the audit doesn't record the returned model identity. Verify the routing before changing anything — don't simply relabel old runs.
> 5. The dashboard's activity isn't fully live. Ordinary model messages and tool history are appended after each agent finishes. Users can see starts and delegations, but intermediate tool activity arrives in batches. The assignment asks to watch what agents are saying and doing while the ticket runs.
> 6. The delegation limit isn't actually shared across the team. Child agents receive copies of the integer counter. Ticket 103 recorded 8 attempts: 7 successful delegations and 1 refusal, despite the documented total limit of six. Use one shared counter and distinguish successful delegations from attempts in the reflection.
> 7. Reset can restore old completed-run information. The database resets, but old run state remains available through memory and the audit. The board can therefore show historical completed summaries beside freshly reopened tickets. Retain the audit, but separate the current reset/run session from earlier ones.
>
> There are also smaller write-up corrections:
> - Ticket 102's Actual section says the Facilities → Accounting path matched; the audit shows Boss → Facilities and Boss → Accounting. Your Reflection correctly explains this, so the two sections contradict each other.
> - Ticket 103 still needs a clear final answer to the discount request, beyond rejecting the restock PO.
> - The next-month-rent reflection example should acknowledge that $160 cannot cover $2,400.
> - Problem 9's prompt log says nothing was lacking, while the write-up describes an earlier failed run that required a prompt fix.
> - The harness still contains outdated "three read-only tools" wording.
>
> What passed: the frontend builds, the backend read routes work, all three smoke outputs match the database, all nine table schemas are documented, and the submitted cash reconciliation is correct: $3,400 − $840 − $2,400 = $160. Your submitted database remains unchanged; the negative-balance failure occurred only in my separate test copy.

### What was lacking after the first attempt

The first full run only worked after a mid-run prompt fix (its first ticket-101 run prepared no payment request), and the resulting system still let concurrent approvals overdraw cash, resolved tickets before the human decision, let agents close tickets through append_ticket_note, ran on "luna" (which Portkey routes to gpt-5.6-luna, not the required gpt-6-luna), batched agent activity instead of streaming it, and did not truly share the delegation cap — so Problem 9 had to be fixed and re-run from a reset.

### Second follow-up prompt

> There is wrong cash math in the Reflection tab. It says paying rent first would leave $1,000, which could not cover the $840 invoice. $1,000 does cover $840, leaving $160. Either payment order covers both obligations; the timing affects when the vendor block clears.
>
> Ticket 103's discount acceptance is claimed without recorded evidence. resolved_tickets.json, README, and Reflection say you accepted 10% off eight hoodies. The audit only records your PO rejection; the ticket notes still say the discount needs human review. Record your actual discount decision through a human decision flow, including who decided, the terms, and the timestamp. Don't invent or backdate evidence.
>
> The completion logic still resolves too broadly. re_evaluate_ticket() resolves any completed run once no payment requests remain pending. Rejecting the hoodie PO therefore closes 103 even though its separate discount decision remains unrecorded. Require an explicit final disposition covering every outstanding decision. For 101, document whether resolution means the invoice issue was handled and the unfulfilled order was explicitly deferred.
>
> The "three problems the team cannot solve" section misses part of the prompt. Explain the tools and agents needed for each problem. Currently it mainly lists missing operations, and its third example bundles price changes, vendor onboarding, and messaging together. Use three distinct problems with concrete additions and responsible agents.
>
> The duplicate-run guard still ignores queued runs. Block both queued and running so rapid start requests cannot launch duplicate teams.

### What was lacking after the second attempt

The gpt-6-luna re-run still resolved tickets once payment requests were decided, even though 103's discount decision and 101's unfulfilled order had no recorded human disposition, and the duplicate-run guard ignored queued runs, so a human decision flow and an explicit final disposition were added and Problem 9 was run again from a reset.

## Problem 10: Reflection

### Prompt(s) typed

> OK, problem 10: reflection.
>
> First, open output/desk_tickets.html and fill in the Reflection tab. Keep the wording natural, but be detailed and thorough. Cover all of these:
> - How did the agents perform on each ticket, and why would you evaluate them that way? Explain what worked well and what could have been better.
> - For each ticket, how did the "Actual" run compare to the "Expected" plan we wrote earlier? Explain what matched, what changed, and why.
> - What would have been similar if we used one agent with tools instead of the five-agent team, and why?
> - Describe three new problems Campus Customs might face that this team could solve with the tools we built. Explain how the agents and tools would handle each one.
> - Describe three new problems Campus Customs might face that this team couldn't solve with the current tools. Explain what's missing and which additional tools and agents we would need.
>
> Tie every answer back to this app and the three tickets we actually ran (101, 102, 103). Use the ticket tabs and the Cash tab on the same page as evidence, including the actual agent actions, delegations, tool calls, approvals, outcomes, and cash changes where relevant.
>
> Make sure the reflection matches the real runs. Don't make up actions or results, and clearly explain how the new problem examples relate to Campus Customs.
>
> A generic AI essay without specific Campus Customs details will score low, so make the answers specific to what happened in our app.

### Follow-up prompt

> (From the same review logged under Problem 9.) Use one shared counter and distinguish successful delegations from attempts in the reflection.
> - Ticket 102's Actual section says the Facilities → Accounting path matched; the audit shows Boss → Facilities and Boss → Accounting. Your Reflection correctly explains this, so the two sections contradict each other.
> - Ticket 103 still needs a clear final answer to the discount request, beyond rejecting the restock PO.
> - The next-month-rent reflection example should acknowledge that $160 cannot cover $2,400.

### What was lacking after the first attempt

The first reflection described the legacy gpt-5.6-luna run, didn't separate delegation attempts from successes, contradicted the ticket 102 Actual section, had no final answer to 103's discount request, and implied next month's rent could be paid from $160, so it was rewritten from the gpt-6-luna re-run.

### Second follow-up prompt

> There is wrong cash math in the Reflection tab. It says paying rent first would leave $1,000, which could not cover the $840 invoice. $1,000 does cover $840, leaving $160. Either payment order covers both obligations; the timing affects when the vendor block clears.
>
> Ticket 103's discount acceptance is claimed without recorded evidence. resolved_tickets.json, README, and Reflection say you accepted 10% off eight hoodies. The audit only records your PO rejection; the ticket notes still say the discount needs human review. Record your actual discount decision through a human decision flow, including who decided, the terms, and the timestamp. Don't invent or backdate evidence.
>
> The completion logic still resolves too broadly. re_evaluate_ticket() resolves any completed run once no payment requests remain pending. Rejecting the hoodie PO therefore closes 103 even though its separate discount decision remains unrecorded. Require an explicit final disposition covering every outstanding decision. For 101, document whether resolution means the invoice issue was handled and the unfulfilled order was explicitly deferred.
>
> The "three problems the team cannot solve" section misses part of the prompt. Explain the tools and agents needed for each problem. Currently it mainly lists missing operations, and its third example bundles price changes, vendor onboarding, and messaging together. Use three distinct problems with concrete additions and responsible agents.
>
> The duplicate-run guard still ignores queued runs. Block both queued and running so rapid start requests cannot launch duplicate teams.

### What was lacking after the second attempt

The rewritten reflection had wrong cash math about payment order, claimed a discount acceptance that wasn't recorded, and its "cannot solve" section bundled several problems without naming the tools and agents each would need.

### Third follow-up prompt

> 1. Give three genuinely new solvable problems. The Reflection currently repeats invoice payment, rent payment, and the hoodie discount, the same three tickets. The prompt asks for new problems. Describe three specific future scenarios, explain which existing tools and agents could handle them, and use the completed tickets as supporting evidence.
> 2. Compare the actual delegation paths with the original Expected plans explicitly. The reflection now mostly says the roles matched, but:
>    - 101 expected Inventory → Accounting; Boss instead contacted both directly.
>    - 102 expected Boss → Facilities → Accounting; Boss initially contacted both specialists directly.
>    - 103 expected Customer Service to be deferred; Boss included it immediately.
>
>    Explain why these differences mattered: parallel work, redundant checks, refused delegations, and the duplicate discount request. Keep the original Expected sections.
> 3. Clarify ticket 102's starting cash. Its reflection says starting checking was $3,400. That was the start of the full run; ticket 102 began with $2,560, after the invoice payment. State both clearly.
>
> These are writing edits; the reviewed runs don't need repeating for them. The previously missing approval evidence and incorrect cash claim are corrected.

### What was lacking after the third attempt

The reflection's "solvable" examples repeated the three completed tickets instead of new problems, it glossed over how the actual delegation paths differed from the Expected plans, and it gave ticket 102 the run's $3,400 starting cash instead of the $2,560 it actually started with.

## Problem 11: Submit to GitHub

### Prompt(s) typed

> OK, problem 11: submit to GitHub.
>
> We are pushing to a public GitHub repository so the grader can clone it. Then we are submitting the repo URL to Canvas and also putting it in output/github_url.txt. Do not push the real .env to the GitHub repo, and do include both database files under data/ (the original and the working copy) so graders can easily run the app.
>
> Make sure the expected layout looks like this:
>
> hw5/
> - AI_prompts.md
> - requirements.txt
> - .env.example
> - .gitignore
> - .mcp.json
> - README.md
> - data/
>   - campus_customs.db
>   - campus_customs_new.db
> - mcp_server/
>   - server.py
>   - README.md
> - frontend/
> - backend/
>   - main.py
>   - models.py
>   - prompts/
>     - boss.md
>     - inventory.md
>     - accounting.md
>     - facilities.md
>     - customer_service.md
> - output/
>   - harness.md
>   - mcp_smoke.json
>   - desk_tickets.html
>   - resolved_tickets.json
>   - resolved_board.html
>   - audit_trail.json
>   - github_url.txt
>
> README.md should also explain how to copy the original DB to the working copy when you need a clean run, start the MCP server, start the FastAPI backend, start the React board, and reset the DB before a full three-ticket run.

### Follow-up prompt

No follow-up prompt was needed.

### What was lacking after the first attempt

Nothing was lacking after the first attempt.
