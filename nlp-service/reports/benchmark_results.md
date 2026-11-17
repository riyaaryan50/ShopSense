# NLP service benchmark results

Embedding engine: `sentence-transformers/all-MiniLM-L6-v2` · data source: `backend`

## Semantic search latency
- 60 queries · mean **12.72 ms** · p50 12.47 ms · p95 **15.18 ms** · max 20.71 ms
- Target < 200 ms: **met**

## Search relevance (expected product in top 3)
- Hit rate@3: **100%** on 15 natural-language queries

| Query | Expected | Top 3 | Hit |
|---|---|---|---|
| something to keep my tea hot during lectures | 14 | [14, 13, 44] | yes |
| boil water for instant noodles in the hostel | 13 | [44, 13, 45] | yes |
| listen to music on the bus | Audio | [8, 32, 35] | yes |
| quiet clicking mouse for the library | 10 | [10, 37, 9] | yes |
| carry my laptop and books to college in the rain | 15 | [15, 16, 48] | yes |
| charge my phone during a power cut | 12 | [47, 12, 18] | yes |
| solve matrices and complex numbers in the engineering exam | 11 | [11, 42, 41] | yes |
| light to read textbooks at night | 17 | [17, 41, 15] | yes |
| print my project report at home | 20 | [43, 20, 41] | yes |
| take handwritten notes on lecture slides with a pen | 5 | [41, 5, 27] | yes |
| move presentation files between computers | 19 | [19, 50, 51] | yes |
| hold my phone upright for video calls | 21 | [21, 38, 28] | yes |
| plug in all my chargers at the study desk | 18 | [18, 12, 47] | yes |
| budget laptop for programming | 3 | [3, 2, 24] | yes |
| type long assignments on a full size keyboard | 9 | [36, 41, 9] | yes |

## Sentiment vs star ratings (100 reviews)
Ground truth: stars 4-5 positive, 3 neutral, 1-2 negative

| Model | 3-class accuracy | Positive vs negative | ms / review |
|---|---|---|---|
| vader | 85% | 93% | 0.077 |
| vader+domain | 82% | 91% | 0.097 |

Per-class (VADER + domain lexicon, used in production): positive 90% (n=70), neutral 9% (n=11), negative 95% (n=19)

Note: the review corpus is synthetic demo data (see backend/scripts/review_bank.py). 3-star reviews are deliberately mixed, so the neutral class is the hardest.

## Chatbot intent classification
- 30 labelled queries · accuracy **100%**
