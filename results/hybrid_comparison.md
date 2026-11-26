# Hybrid search with reciprocal rank fusion

Hit rate @3 -> BM25: 6/10 | Vector: 8/10 | Hybrid: 8/10

Best weight: 0.5 (share of BM25, the rest is vector).

| Question | Type | BM25 | Vector | Hybrid |
|---|---|---|---|---|
| What is policy HR-204 about? | keyword | Y | Y | Y |
| Who owns IT-117? | keyword | N | Y | Y |
| Show the details of employee E047 | keyword | Y | N | N |
| Which leave did E118 take on 2026-07-26? | keyword | Y | Y | Y |
| Do company laptops use BitLocker? | keyword | Y | Y | Y |
| Can I keep my unused vacation days for next year? | meaning | Y | N | Y |
| What should I do if I fell for a fake email? | meaning | N | Y | N |
| How much more money do I get when I am promoted? | meaning | N | Y | Y |
| Am I allowed to work from my hometown for a few weeks? | meaning | Y | Y | Y |
| What happens if I keep coming to the office late? | meaning | N | Y | Y |

## Weight sweep

| BM25 weight | Hybrid hits @3 |
|---|---|
| 0.0 | 8/10 |
| 0.2 | 8/10 |
| 0.3 | 8/10 |
| 0.4 | 8/10 |
| 0.5 | 8/10 |
| 0.6 | 8/10 |
| 0.7 | 8/10 |
| 0.8 | 8/10 |
| 1.0 | 6/10 |
