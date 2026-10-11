# Campus Customs dashboard design

The three-column desk layout gives each kind of work a clear home: tickets on the left, the active shop floor in the middle, and manager controls on the right. This keeps selection, live operations, and money decisions visible together at laptop width, so a manager does not have to switch views while a run is active.

Boss is the central hub because every ticket begins with routing and reconciliation there. The four specialists surround that desk in a fixed two-row arrangement, which makes the flow of responsibility legible and prevents the characters or their station props from colliding.

Each role has a muted clothing colour and a small SVG prop chosen to explain its job at a glance: Inventory has folded hoodies and boxes, Accounting has a calculator and receipts, Facilities has keys and lease papers, Customer Service has an open laptop, and Boss has a clipboard. These details make the scene feel like a working campus shop while keeping names, statuses, and live speech readable.

The corkboard uses clothing-tag ticket IDs because the queue is a merchandise-shop queue, not a generic task list. The selected card lifts with an amber edge to make the current work obvious, while a rotated RESOLVED stamp communicates completion without competing with the ticket subject.

Approval requests look like receipts because they are concrete cash decisions rather than conversational messages. Amber is reserved for approval actions and the balance card flashes amber when a real approved payment changes checking, giving the human a short visual confirmation without implying simulated activity.

The activity feed and run summary sit beneath and beside the scene so the shop remains the focal point while the evidence stays available. Feed entries are derived from real event payloads, summaries clean the backend text and offer a small more/less control, and reloads recover the latest run from the backend. Speech bubbles and delegation notes are intentionally brief and disappear after a run; reduced-motion preferences disable the remaining animation so motion supports attention rather than distracting from the audit trail.
The refined shop floor uses lighter outlined SVG props rather than dark blocks: folded hoodies and a kraft box identify Inventory, a calculator and receipt identify Accounting, keys and a lease page identify Facilities, a blue-screen laptop identifies Customer Service, and a checklist clipboard identifies Boss. Consistent role colours and small accessories—a tie, apron, visor, lanyard, and headset—make the five staff recognizable even when their stations are idle. A back-wall hoodie shelf, plant, rug, perspective floorboards, and station shadows add depth without competing with the live labels.

The refined corkboard puts a compact request-outcome chip under each ticket, connecting the visual queue to the real `/requests` history. The manager's desk combines the balance with a payments ledger computed from `/payments`, a calculated opening balance, and a collapsible decision history showing paid and rejected receipts. This gives the human both pending decisions and the completed cash trail in the same place.

The header exposes the database shop date and current run state, while the activity feed has role filters and a compact view for dense runs. The dashboard refreshes more frequently during active runs and less frequently while idle, and retains the existing focus rings, readable contrast, human-readable speech gists, and reduced-motion behavior.

Agent runs use Portkey's `gpt-6-luna` model. Each model response records the provider-returned identity in the live audit feed, making model routing visible in the run evidence without exposing credentials.

### Yale campus details

The shop now uses Yale Blue (`#00356B`) as its navy anchor, with an original triangular pennant carrying a collegiate Y and a small BULLDOGS pennant, a pointed-arch leaded window, and an elm-leaf garland draped along the sign to suggest New Haven without copying official Yale branding. The back shelf and Inventory goods use Yale Blue and white hoodies, including a tiny Y detail. A simple original English bulldog rests at floor level between Boss and Customer Service with a Yale Blue collar and Y tag; its small tail movement is disabled by reduced-motion preferences. These additions are intentionally placed around the existing sign and stations so labels, receipts, and the balance remain the visual priorities.
