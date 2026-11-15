# NLP service benchmark results

Embedding engine: `sentence-transformers/all-MiniLM-L6-v2` · data source: `backend`

## Semantic search latency
- 60 queries · mean **14.13 ms** · p50 13.68 ms · p95 **20.99 ms** · max 27.25 ms
- Target < 200 ms: **met**

## Search relevance (expected product in top 3)
- Hit rate@3: **100%** on 15 natural-language queries

| Query | Expected | Top 3 | Hit |
|---|---|---|---|
| something to keep my tea hot during lectures | 14 | [14, 13, 17] | yes |
| boil water for instant noodles in the hostel | 13 | [13, 14, 15] | yes |
| listen to music on the bus | 7 | [8, 4, 7] | yes |
| quiet clicking mouse for the library | 10 | [10, 9, 7] | yes |
| carry my laptop and books to college in the rain | 15 | [15, 16, 14] | yes |
| charge my phone during a power cut | 12 | [12, 18, 6] | yes |
| solve matrices and complex numbers in the engineering exam | 11 | [11, 12, 15] | yes |
| light to read textbooks at night | 17 | [17, 15, 4] | yes |
| print my project report at home | 20 | [20, 18, 13] | yes |
| take handwritten notes on lecture slides with a pen | 5 | [5, 4, 19] | yes |
| move presentation files between computers | 19 | [19, 4, 18] | yes |
| hold my phone upright for video calls | 21 | [21, 4, 6] | yes |
| plug in all my chargers at the study desk | 18 | [18, 12, 11] | yes |
| budget laptop for programming | 3 | [3, 2, 5] | yes |
| type long assignments on a full size keyboard | 9 | [9, 11, 17] | yes |

## Sentiment vs star ratings (100 reviews)
Ground truth: stars 4-5 positive, 3 neutral, 1-2 negative

| Model | 3-class accuracy | Positive vs negative | ms / review |
|---|---|---|---|
| vader | 85% | 93% | 0.074 |
| vader+domain | 82% | 91% | 0.08 |
| distilbert | 56% | 63% | 24.325 |

Per-class (VADER + domain lexicon, used in production): positive 90% (n=70), neutral 9% (n=11), negative 95% (n=19)

Note: the review corpus is synthetic demo data (see backend/scripts/review_bank.py). 3-star reviews are deliberately mixed, so the neutral class is the hardest.

## Chatbot intent classification
- 30 labelled queries · accuracy **100%**
