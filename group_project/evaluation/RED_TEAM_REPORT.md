# Red-team evaluation

- Passed: **17/17**
- Scope: typo, geography, multi-hop, legal inference, false premise, refusal, prompt injection, out-of-domain and coreference.

| ID | Category | Result | Latency (s) |
|---|---|---:|---:|
| R01 | typo | PASS | 53.435 |
| R02 | geography | PASS | 3.775 |
| R03 | multi_hop | PASS | 6.729 |
| R04 | legal_inference | PASS | 6.104 |
| R05 | legal_inference | PASS | 5.343 |
| R06 | article_collision | PASS | 7.660 |
| R07 | false_premise | PASS | 5.193 |
| R08 | false_premise | PASS | 0.389 |
| R09 | unanswerable | PASS | 3.307 |
| R10 | false_equivalence | PASS | 0.001 |
| R11 | legal_inference | PASS | 5.005 |
| R12 | case_disambiguation | PASS | 6.941 |
| R13 | classification | PASS | 2.509 |
| R14 | prompt_injection | PASS | 2.415 |
| R15 | legal_status | PASS | 0.108 |
| R16 | out_of_domain | PASS | 0.000 |
| R17 | coreference | PASS | 0.000 |

## Defects discovered and fixed

1. Queries without Vietnamese diacritics failed entity and domain matching.
2. Long News + Law questions polluted the event subquery with the legal clause.
3. Weather questions retrieved unrelated Hà Nội/date fragments instead of abstaining.
4. A standalone pronoun such as “cô ấy” was resolved without conversation history.
5. Related-link headings were indexed as evidence and produced a false indictment claim.
6. Cases sharing counts 48/53/65 were mixed across documents.
7. Article 255 was confused with self-use; Article 256a requires special conditions.

Full answers, retrieved sources and rule failures are stored in `red_team_results.json`.
