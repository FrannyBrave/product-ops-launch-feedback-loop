# Launch & Feedback Loop: A Cross-Team Process Design

> **Concept design.** I wrote this process to show how I'd connect a product team with its customer-facing teams. It isn't documentation of a process at a real employer. The sample company, "Brightline," is fictional.

**Author:** Francesca Djoufack

---

## The problem

When a B2B software company grows fast, two gaps open up at the same time:

1. **Product → customer-facing teams.** Support, Sales and Implementations find out about changes late, or from customers. They aren't ready to configure, train or answer questions.
2. **Customer-facing teams → product.** Customer issues and requests arrive through Slack DMs, support tickets, sales calls and hallway conversations. They reach the wrong PM, lose their context, or disappear. And the person who raised them never hears what happened.

This process closes both gaps with **one launch path out** and **one intake path in**, and uses AI to keep information moving so nobody needs extra meetings.

## Design principles

- **Fewer, better processes.** One launch checklist, one intake path. If a step has no owner and no clear reason, it gets deleted.
- **Scale effort to impact.** A small fix shouldn't go through the same process as a change that needs customer configuration and training.
- **Async first.** Briefings, digests and status updates replace standing meetings.
- **AI drafts, people decide.** Automations write first drafts and route information. A person reviews anything that reaches a customer or changes a priority.
- **Flag, don't guess.** If information is missing, the workflow asks for it instead of filling the gap.
- **Always close the loop.** Every request gets an answer back to the person who raised it, even if the answer is "not now."
- **Built to outlast its designer.** Owned by roles, not people, written down, and partly automated.

---

## Part 1: Product → customer-facing teams (launch readiness)

### Launch tiers

| Tier | What it covers | What's required |
|---|---|---|
| **Tier 1** | Changes that need customer configuration, training or a planned rollout (typical for enterprise customers) | Launch brief, team briefings, early access, customer communication plan, launch review |
| **Tier 2** | Notable new features or workflow changes | Launch brief, team briefings, release notes |
| **Tier 3** | Small improvements and fixes | Release notes only |

The PM assigns the tier when the work is planned, so everyone knows early how much preparation a change needs.

### Stages

| Stage | When | Owner | Output |
|---|---|---|---|
| **1. Flag** | When the work is planned | PM | Tier assigned on the ticket |
| **2. Brief** | Tier 1: 2 weeks before release. Tier 2: 1 week before | PM, with an AI-drafted starting point | Launch brief (template below) |
| **3. Enable** | 1 week before release | Product Ops | Team briefings for Support, Sales and Implementations, drafted by AI and reviewed by the PM |
| **4. Early access** (Tier 1) | Before general release | Implementations + PM | A small group of customers tries the change; feedback comes back through the intake path |
| **5. Ship & announce** | Release day | Product Ops | Customer release notes published; internal briefing posted in the release Slack channel |
| **6. Close the loop** | 2 weeks after release | Product Ops | Short launch review (below) |

### Launch brief template

- **What's changing**, in one or two sentences
- **Why**: the customer problem it solves
- **Who's affected**: which customers, roles or plans
- **What customers need to do**: configuration, training, nothing
- **Risks and known limitations**
- **Likely questions**, with answers
- **Owner and release date**

### Tier 1 readiness checklist

- [ ] Launch brief complete and reviewed
- [ ] Support briefing sent, including what to watch for
- [ ] Sales talking points sent
- [ ] Implementations has configuration steps and a rollout plan for affected customers
- [ ] Early-access customers identified, and their feedback reviewed
- [ ] Customer communication drafted and approved
- [ ] Rollback or mitigation plan agreed with Engineering

### Launch review (2 weeks after release)

Three questions, answered asynchronously in the launch's Slack thread:

1. Are the customers we expected using it?
2. What did Support hear about it, and how many tickets came in?
3. What would we do differently next time?

---

## Part 2: Customer-facing teams → product (feedback intake)

### One front door

Every customer issue, request or piece of feedback goes through **one intake form** (for example, a Slack workflow, or a Zendesk tag that syncs across). Required fields:

- Customer
- Type: bug, feature request, question, or other
- What happened, in the customer's words if possible
- Business impact for the customer
- Urgency
- Link to evidence (ticket, call notes, screenshot)

**Not in scope:** urgent production issues. Those stay on the existing support escalation path, so this process never slows down an emergency.

### Triage (daily, AI-assisted)

1. **Classify** each item by type, product area and urgency.
2. **Route** it to the PM who owns that product area, using the routing table.
3. **Group** duplicates and related items into themes across customers.
4. **Flag** anything incomplete or unclear, and send a specific question back to the person who submitted it.

### Routing table

| Product area | Owner |
|---|---|
| Loan pipeline | PM, Pipeline |
| Document management | PM, Documents |
| Borrower portal | PM, Borrower Experience |
| Integrations | PM, Platform |
| Unclear | Product Ops reviews by hand |

### Closing the loop

| PM decision | What the requester hears |
|---|---|
| Planned | Expected timing, and a note when it ships |
| Not now | The reason, so they can explain it to the customer |
| Need more info | The specific question |
| Shipped | A notification, with the release note to share |

### Weekly themes digest

Each week, every PM gets a short digest: recurring themes, how many customers raised each one, example quotes, and links back to the original items. Patterns surface without anyone digging through tickets.

---

## Roles

| Role | Responsibilities |
|---|---|
| **PM** | Assigns launch tiers, writes or approves launch briefs, reviews AI drafts, decides on routed feedback |
| **Product Ops** | Owns and improves the process, runs the automations, publishes briefings and release notes, runs launch reviews and the themes digest |
| **Support, Sales, Implementations** | Submit feedback through the front door, read briefings, prepare customers for Tier 1 changes |
| **Engineering** | Confirms release dates and risks, and agrees on rollback plans for Tier 1 launches |

---

## Where AI fits, and its guardrails

| Step | What AI does | What a person does |
|---|---|---|
| Launch brief | Drafts it from tickets and specs | PM edits and approves it |
| Team briefings and release notes | Drafts versions for each audience | PM reviews; Product Ops publishes |
| Feedback triage | Classifies, routes, groups themes | Product Ops spot-checks; PM decides |
| Missing information | Flags gaps and drafts questions | The submitter or PM answers |

**Guardrails**
- Nothing reaches a customer without a person reviewing it.
- The AI only uses the information it's given. Gaps are flagged, not filled in.
- Every summary links back to its source item, so anyone can check it.
- Only approved AI tools are used, and only the customer details each step needs.

---

## Success metrics

Example targets I would set, then adjust after the first month:

**Launch readiness**
- Share of Tier 1 and Tier 2 launches briefed on time (target: 90%+)
- Support tickets saying "we didn't know about this change" (target: trending toward zero)
- Customer-facing teams rating their launch readiness in a quarterly pulse survey

**Feedback intake**
- Time from submission to PM acknowledgment (target: within 5 business days)
- Share of items routed to the right PM the first time
- Share of requesters who get a closing update
- Standing meetings this process lets the team cancel

---

## Rolling out the process itself

1. **Pilot** with one product area and one customer-facing team for 30 days.
2. **Adjust** based on what the pilot teams say is friction and what the metrics show.
3. **Write it down**: this document, the templates and the routing table live in one shared place, owned by a role.
4. **Expand** to the remaining product areas.
5. **Review quarterly**, including a "what can we delete?" check, so the process stays lean after I'm no longer the one running it.
