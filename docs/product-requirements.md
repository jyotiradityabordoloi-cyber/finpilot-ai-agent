\# FinPilot — Product Requirements



\## 1. Product



FinPilot is an AI-powered month-end close investigation agent.



\## 2. Problem



Finance and operations teams spend significant time manually reviewing

transactions, matching supporting documents, investigating unusual spending,

and identifying exceptions before month-end close.



The challenge is not simply calculating financial values. The challenge is

investigating exceptions across fragmented financial information and

determining which issues require human attention.



\## 3. Target User



Finance and operations professionals at small and growing businesses.



\## 4. Core Job To Be Done



"Help me identify and investigate the financial exceptions I need to review

before closing the month."



\## 5. MVP



The MVP will allow a user to:



1\. Load financial transactions.

2\. Analyze transaction patterns.

3\. Detect potential anomalies.

4\. Match transactions against invoices.

5\. Identify mismatches and missing documentation.

6\. Investigate high-priority exceptions.

7\. Produce evidence-backed findings.

8\. Allow a human to review and resolve findings.



\## 6. AI Role



AI will be responsible for:



\- Investigation planning

\- Tool selection

\- Evidence synthesis

\- Finding explanation

\- Prioritization

\- Natural-language responses



\## 7. Non-AI Responsibilities



Deterministic Python logic will handle:



\- Financial calculations

\- Transaction aggregation

\- Duplicate detection

\- Transaction-to-invoice matching

\- Statistical analysis

\- Data validation



\## 8. Human-in-the-Loop



FinPilot will not:



\- Move money

\- Approve payments

\- Modify accounting records

\- Automatically close financial periods



Financial decisions remain subject to human review.



\## 9. Initial Exception Types



The prototype will detect:



\- Duplicate payments

\- Invoice mismatches

\- Missing invoices

\- Unusual vendor spending

\- Unknown vendors

\- Unexpected category changes



\## 10. Success Metrics



The prototype will measure:



\- Exception detection precision

\- Exception detection recall

\- False-positive rate

\- Evidence accuracy

\- Investigation completion rate

\- Estimated investigation time saved



\## 11. Constraints



The prototype should be deployable at zero infrastructure cost

using free tiers and open-source technologies where practical.



The prototype will use synthetic financial data only.



\## 12. Product Principle



Automate repetitive investigation work while keeping consequential

financial decisions under human control.

