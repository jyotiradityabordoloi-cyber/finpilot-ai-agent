\# FinPilot — AI Opportunity Map



\## Purpose



FinPilot should not use AI simply because AI is available.



Each part of the month-end financial workflow should be evaluated based

on whether AI provides meaningful value compared with deterministic

software or human judgment.



\## Decision Framework



We divide the workflow into three categories:



\### 1. Automate



Use deterministic software when the task has a clear set of rules and

does not require interpretation.



\### 2. AI-Assisted



Use AI when the task requires reasoning, interpretation, investigation,

or synthesis across multiple sources.



\### 3. Human-Controlled



Keep humans responsible for decisions that could have significant

financial or operational consequences.





\## Workflow Mapping



| Workflow | Approach | Reason |

|---|---|---|

| Data validation | Automation | Rule-based |

| Transaction calculations | Automation | Deterministic |

| Duplicate detection | Automation | Pattern/rule based |

| Invoice matching | Automation + AI | Matching can be deterministic; ambiguous cases may require AI |

| Historical spending analysis | Automation | Statistical calculation |

| Anomaly investigation | AI-assisted | Requires contextual reasoning |

| Evidence synthesis | AI-assisted | Combines multiple information sources |

| Finding explanation | AI-assisted | Natural-language reasoning |

| Exception prioritization | AI-assisted | Requires context and judgment |

| Payment approval | Human-controlled | High financial consequence |

| Accounting record modification | Human-controlled | High consequence |

| Money movement | Human-controlled | High consequence |







\## Where AI Creates the Most Value



The highest-value AI opportunity is not document extraction.



It is \*\*exception investigation\*\*.



For example:



A transaction is detected as unusual.



The deterministic system can identify:



\- Transaction amount

\- Historical average

\- Vendor

\- Category

\- Invoice amount

\- Difference



The AI agent can then reason across these results and answer:



> Why might this transaction require attention?



It can gather evidence, explain the discrepancy, and recommend a next

step.





\## Example



\### Input



Transaction:



\- Vendor: AWS

\- Amount: ₹87,500



Historical AWS spending:



\- May: ₹12,200

\- June: ₹13,100

\- July: ₹13,600



Matching invoice:



\- Amount: ₹53,100



\### Deterministic Layer



Python calculates:



\- Historical average

\- Spending deviation

\- Invoice difference

\- Matching confidence



\### AI Layer



The agent interprets the evidence and generates:



> High-priority exception. The AWS transaction is significantly above

> recent historical spending and exceeds the available invoice amount.

> Review the transaction and supporting documentation before

> reconciliation.



\### Human Layer



The user decides whether the transaction is legitimate and what action

to take.







\## Why Not Use AI Everywhere?



Using an LLM for deterministic financial calculations creates unnecessary

risk.



For example:



Bad approach:



```text

LLM → calculate financial difference → make decision

