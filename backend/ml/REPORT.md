# B1 report (fill with YOUR numbers; keep it short)

## Data findings
- Size/shape: <rows>, <#categories>, <#intents>; balance: <balanced / skewed, how>.
- Duplicates: <N> exact, <M> after normalising -> dropped (kept 1 copy).
- Label conflicts: <K> texts with >1 category -> removed.
- Doubtful labels: <e.g. DELIVERY vs SHIPPING overlap; where "cancel my order" sits vs CANCEL>. Kept the dataset's labels, expected confusion here.
- Near-duplicates: dataset is template-augmented. Random split: <X>% of test had a >=0.9 neighbour in train; group split: <Y>%.  (python -m ml.leak_check)

## Split (why it does not leak)
Group-aware StratifiedGroupKFold (cosine >= <thr>, <G> groups, largest <S>%); asserts show no group/text in both train and test;
hyper-parameters chosen on validation; test scored once. Limit: paraphrases below the threshold can still cross the split.

## Scores
| Model | Test acc | Test macro-F1 | Messy-20 |
|---|---|---|---|
| TF-IDF + LR (baseline) | | | |
| DistilBERT | | | |

## Five wrong predictions
| # | Text | True | Pred (conf) | Why wrong | What I would do |
|---|---|---|---|---|---|
| 1 | | | | | |
