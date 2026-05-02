# SOAPFlow evaluation comparison

Generated: 2026-05-02T02:52:20

## Aggregate metrics

| Run | n | Success | ROUGE-L | ROUGE-1 | BLEU | Sections | Latency (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| demo (test.jsonl) | 57 | 57/57 | 0.0947 | 0.1819 | 0.0050 | 4.00 | 2 |
| mlx (test.jsonl) | 57 | 57/57 | 0.0827 | 0.1438 | 0.0062 | 3.40 | 26747 |
| mlx (test.jsonl) | 57 | 57/57 | 0.0155 | 0.0156 | 0.0000 | 0.04 | 11414 |
| mlx (test.jsonl) | 57 | 57/57 | 0.0150 | 0.0150 | 0.0000 | 0.00 | 4425 |

## Per-source ROUGE-L

| Run | Source | n | ROUGE-L | ROUGE-1 | Sections |
| --- | --- | ---: | ---: | ---: | ---: |
| demo (test.jsonl) | primock57 | 57/57 | 0.0947 | 0.1819 | 4.00 |
| mlx (test.jsonl) | primock57 | 57/57 | 0.0827 | 0.1438 | 3.40 |
| mlx (test.jsonl) | primock57 | 57/57 | 0.0155 | 0.0156 | 0.04 |
| mlx (test.jsonl) | primock57 | 57/57 | 0.0150 | 0.0150 | 0.00 |

## Reports

- **demo (test.jsonl)** — `data/splits/test.jsonl` (57 examples)
- **mlx (test.jsonl)** — `data/splits/test.jsonl` (57 examples)
- **mlx (test.jsonl)** — `/Users/sushildalavi/Desktop/Github/SOAPFlow/data/splits/test.jsonl` (57 examples)
- **mlx (test.jsonl)** — `/Users/sushildalavi/Desktop/Github/SOAPFlow/data/splits/test.jsonl` (57 examples)
