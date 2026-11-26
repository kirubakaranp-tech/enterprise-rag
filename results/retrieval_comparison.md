# BM25 vs vector search

A hit means the chunk with the answer is in the top 3.

BM25: 6/10 | Vector: 8/10

| Question | Type | BM25 hit (Y/N) | Vector hit (Y/N) |
|---|---|---|---|
| What is policy HR-204 about? | keyword | Y | Y |
| Who owns IT-117? | keyword | N | Y |
| Show the details of employee E047 | keyword | Y | N |
| Which leave did E118 take on 2026-07-26? | keyword | Y | Y |
| Do company laptops use BitLocker? | keyword | Y | Y |
| Can I keep my unused vacation days for next year? | meaning | Y | N |
| What should I do if I fell for a fake email? | meaning | N | Y |
| How much more money do I get when I am promoted? | meaning | N | Y |
| Am I allowed to work from my hometown for a few weeks? | meaning | Y | Y |
| What happens if I keep coming to the office late? | meaning | N | Y |
