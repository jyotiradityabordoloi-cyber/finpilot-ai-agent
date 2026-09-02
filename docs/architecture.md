\# FinPilot — System Architecture



\## 1. Architecture Overview



FinPilot is designed as a production-style AI financial investigation

system using a deterministic financial analysis layer and an AI agent

orchestration layer.



The prototype will use synthetic financial data and free/open-source

technologies where practical.



\## 2. High-Level Architecture



User

&#x20; |

&#x20; v

Streamlit Interface

&#x20; |

&#x20; v

FinPilot Agent

&#x20; |

&#x20; v

LangGraph Orchestration

&#x20; |

&#x20; +-------------------+

&#x20; |                   |

&#x20; v                   v

Deterministic Tools   AI Reasoning

&#x20; |                   |

&#x20; +---------+---------+

&#x20;           |

&#x20;           v

&#x20;      Evidence Layer

&#x20;           |

&#x20;           v

&#x20;    Investigation Result

&#x20;           |

&#x20;           v

&#x20;      Human Review



\## 3. Application Layers



\### Presentation Layer



Technology:

\- Streamlit



Responsibilities:

\- Display financial dashboard

\- Accept user requests

\- Display findings

\- Display evidence

\- Allow human review

\- Display investigation status



\### Agent Layer



Technology:

\- LangGraph

\- LangChain components where useful



Responsibilities:

\- Understand user intent

\- Plan investigation

\- Select appropriate tools

\- Maintain investigation state

\- Evaluate tool results

\- Decide whether additional investigation is required

\- Produce structured findings



\### Deterministic Financial Layer



Technology:

\- Python

\- Pandas



Responsibilities:

\- Financial calculations

\- Transaction aggregation

\- Duplicate detection

\- Invoice matching

\- Historical comparisons

\- Data validation

\- Statistical anomaly detection



Financial calculations should not depend on LLM-generated arithmetic.



\### Data Layer



Initial prototype:

\- CSV files



Potential production architecture:

\- PostgreSQL database

\- Object storage for documents



The prototype will use synthetic data only.



\### Evidence Layer



The evidence layer stores the information used to support an AI finding.



Evidence may include:

\- Transaction records

\- Invoice records

\- Historical spending

\- Vendor information

\- Uploaded financial documents



AI findings should reference the evidence used to produce them.



\## 4. Agent Workflow



A typical investigation will follow this workflow:



1\. User submits a financial review request.

2\. Agent interprets the request.

3\. Agent creates an investigation plan.

4\. Agent calls deterministic financial tools.

5\. Tools return structured results.

6\. Agent evaluates the results.

7\. Agent requests additional evidence if necessary.

8\. Agent synthesizes the evidence.

9\. Agent generates a structured finding.

10\. Human reviews the finding.

11\. Finding is resolved or escalated.



\## 5. Initial Agent Tools



\### Transaction Analysis Tool



Purpose:

Analyze transaction history and identify unusual patterns.



\### Duplicate Detection Tool



Purpose:

Identify potentially duplicated payments.



\### Invoice Matching Tool



Purpose:

Compare transactions with invoices.



\### Historical Spending Tool



Purpose:

Compare current spending with historical vendor or category spending.



\### Missing Documentation Tool



Purpose:

Identify transactions without supporting invoices or receipts.



\### Vendor Analysis Tool



Purpose:

Analyze vendor activity and identify unexpected vendors or changes.



\## 6. Agent State



The agent should maintain structured state during an investigation.



Example:



transaction\_id:

TXN-00482



vendor:

AWS



transaction\_amount:

87500



historical\_average:

13200



invoice\_amount:

53100



difference:

34400



evidence:

\- transaction record

\- invoice record

\- historical transactions



finding\_type:

invoice\_mismatch



severity:

high



status:

needs\_human\_review



\## 7. AI Responsibilities



The AI model may:



\- Interpret natural-language requests

\- Plan investigations

\- Select tools

\- Interpret structured tool results

\- Combine multiple evidence sources

\- Explain findings

\- Prioritize exceptions

\- Generate recommended next steps



\## 8. AI Restrictions



The AI model should not:



\- Perform critical financial calculations when deterministic code can do so

\- Invent financial evidence

\- Modify financial records

\- Approve payments

\- Move money

\- Automatically close accounting periods



\## 9. Human-in-the-Loop



Human approval is required for consequential financial decisions.



FinPilot provides investigation assistance rather than autonomous financial

decision-making.



\## 10. Error Handling



The system should handle:



\- Missing data

\- Invalid transaction records

\- Missing invoices

\- Ambiguous matches

\- Tool failures

\- AI failures

\- Unsupported requests



When evidence is insufficient, FinPilot should explicitly communicate

uncertainty rather than inventing an answer.



\## 11. Evaluation



The system will use a synthetic dataset with known ground-truth issues.



Evaluation will measure:



\- Precision

\- Recall

\- False-positive rate

\- Evidence accuracy

\- Investigation completion

\- Response reliability



\## 12. Deployment



Target prototype architecture:



GitHub

&#x20; |

&#x20; v

Streamlit Community Cloud

&#x20; |

&#x20; v

FinPilot Application



The initial prototype should operate within free-tier infrastructure

where practical.



\## 13. Security Principles



The prototype will:



\- Use synthetic financial data

\- Keep API keys outside source code

\- Use environment variables for secrets

\- Exclude secrets from Git

\- Avoid storing real financial information



\## 14. Architectural Principle



Use deterministic software for deterministic financial operations.



Use AI for reasoning, investigation, interpretation, and explanation.



Keep humans responsible for consequential financial decisions.

