import pandas as pd

csv_file = "output/questions_v2_100/analysis.csv"
df = pd.read_csv(csv_file)


stats = df.groupby("model")[["score_bleu", "score_rouge_l", "score_bert"]].agg(
    ["mean", "std", "count"]
)
n = df["patient_id"].nunique()

stats.columns = [f"{col[0]}_{col[1]}" for col in stats.columns]

for metric in ["score_bleu", "score_rouge_l", "score_bert"]:
    stats[f"{metric}_formatted"] = stats.apply(
        lambda row: f"{row[f'{metric}_mean']:.3f} \\pm {row[f'{metric}_std']:.3f}",
        axis=1,
    )
latex_df = stats[
    ["score_bleu_formatted", "score_rouge_l_formatted", "score_bert_formatted"]
]
latex_df.columns = ["BLEU", "ROUGE-L", "BERT"]

latex_table = latex_df.to_latex(
    escape=False,
    caption=f"Performance comparison of RAG models (n={n})",
    label="tab:model_performance",
)

print(latex_table)
