# Eval Scorecard

Generated: 2026-09-07 | Answer model: `gpt-4.1-mini` | Judge: `gpt-4.1` | k = 5

## Summary

- Questions run: **20** of 20
- Retrieval hit-rate: **15/20** (75%)
- Answer grades: **9 correct**, 7 partial, 4 incorrect

## Per-question results

| # | Report | Question | Hit | Gold p. | Retrieved p. | Grade | Judge note |
|---|--------|----------|-----|---------|--------------|-------|------------|
| 1 | NFLX_AR2025 | How much did Netflix's revenue grow in 2025? | ✅ | 29 | 49, 29, 51, 50, 31, 5, 54 | CORRECT | All material facts are present with matching numbers and correct percentages, just at higher precision. |
| 2 | CRM_AR2026 | What was Salesforce's total revenue in fiscal 2026? | ✅ | 2, 5, 46, 47, 52 | 67, 68, 71, 2, 111, 47, 80 | PARTIAL | The assistant gives the correct total revenue but omits the 10% year-over-year increase. |
| 3 | NFLX_AR2025 | What was Netflix's operating margin in 2025 and how did it compare to 2024? | ✅ | 29 | 49, 29, 50, 52, 51, 82 | CORRECT | All material facts and numbers from the gold answer are present and accurate. |
| 4 | NFLX_AR2025 | What was Netflix's net income in 2025? | ✅ | 29, 49, 51 | 49, 50, 52, 51, 54, 80, 29 | CORRECT | All material facts from the gold answer are present and accurate, with extra detail that does not contradict. |
| 5 | NFLX_AR2025 | How many paid memberships did Netflix have at the end of 2025? | ✅ | 29 | 49, 29, 52, 5, 71, 60, 41 | CORRECT | The assistant accurately states that membership numbers are not disclosed and matches the gold answer's explanation. |
| 6 | NFLX_AR2025 | How much cash did Netflix spend on additions to content assets in 2025? | ✅ | 51 | 52, 71, 51, 49, 37, 54 | CORRECT | All material facts from the gold answer are present and accurate. |
| 7 | NFLX_AR2025 | What drove Netflix's revenue growth in 2025? | ✅ | 29, 30 | 49, 5, 29, 57, 31, 30 | PARTIAL | The assistant omits the 16% revenue growth figure stated in the gold answer. |
| 8 | NFLX_AR2025 | How much stock did Netflix repurchase in 2025? | ❌ | 51 | 27, 73, 53, 52, 43, 35, 75 | PARTIAL | The assistant gives the 2025 repurchase amount correctly but omits the 2024 figure and the increase. |
| 9 | CRM_AR2026 | What share of Salesforce's total revenue came from subscription and support in fiscal 2026? | ✅ | 47 | 53, 67, 47, 45, 46 | CORRECT | All material facts are present and accurate. |
| 10 | CRM_AR2026 | What was Salesforce's total remaining performance obligation at the end of fiscal 2026? | ❌ | 3, 5, 47 | 80, 52, 66, 45 | PARTIAL | The assistant gives the correct $72.4 billion figure but omits the 14% year-over-year growth and the as-of date, and adds prior year data not in the gold answer. |
| 11 | CRM_AR2026 | When did Salesforce acquire Informatica and what was the purchase consideration? | ✅ | 47, 64 | 87, 88, 86, 14, 47, 57 | CORRECT | All material facts, including date and amount, are accurately stated. |
| 12 | CRM_AR2026 | How much revenue did Informatica contribute to Salesforce in fiscal 2026? | ✅ | 47, 52 | 47, 79, 5, 46, 53, 65 | INCORRECT | The assistant gives $388 million instead of $399 million, which is a material numerical error. |
| 13 | CRM_AR2026 | How much did Salesforce return to stockholders in fiscal 2026? | ❌ | 5, 47, 70 | 45, 67, 69, 71, 44, 65 | INCORRECT | The assistant does not state the total dollar amount of share repurchases ($12.6 billion) and instead gives only share counts and authorization figures. |
| 14 | CRM_AR2026 | What traction did Salesforce report for Agentforce? | ✅ | 2, 3 | 111, 2, 4, 1, 112, 65 | INCORRECT | The assistant gives an incorrect ARR growth rate (169% vs. 200%) and adds an ARR dollar figure not in the gold answer. |
| 15 | MU_AR2025 | What was Micron's total revenue in fiscal 2025 and how did it change? | ✅ | 53, 54, 65, 90 | 65, 66, 69, 67, 51, 41 | CORRECT | All material facts from the gold answer are present and accurate, with extra detail that does not contradict. |
| 16 | MU_AR2025 | How much revenue did Micron's DRAM products generate in fiscal 2025? | ❌ | 53, 90 | 9, 52, 8, 6, 70 | PARTIAL | The assistant gives the correct revenue numbers but omits the 62% sales increase. |
| 17 | MU_AR2025 | What was Micron's net income in fiscal 2025? | ✅ | 53, 65 | 65, 66, 69, 67, 51, 70 | CORRECT | All material facts from the gold answer are present and accurate; extra detail does not contradict. |
| 18 | MU_AR2025 | How much did Micron spend on capital expenditures in fiscal 2025? | ❌ | 59 | 65, 69, 67, 6, 51, 70, 19 | PARTIAL | The assistant gives the correct capital expenditures for 2025 but omits the $2.01 billion in government incentives. |
| 19 | MU_AR2025 | How concentrated is Micron's revenue by customer and end market? | ✅ | 13, 33 | 65, 66, 70, 67, 69, 33, 95 | INCORRECT | The assistant incorrectly attributes the top ten customer concentration to fiscal 2025 only, while the gold answer specifies it was for each of the last three years. |
| 20 | MU_AR2025 | What are Micron's four business units? | ✅ | 8 | 8, 65, 18, 22, 67, 41 | PARTIAL | The assistant lists all four business units accurately but omits the material fact that these units were formed following a reorganization in Q4 FY2025. |
