def generate_parsing_report(run_id: str, metrics_summary: dict) -> str:
    """
    Génère un rapport Markdown pour une expérience de Parsing.
    """
    report = f"# Rapport d'Évaluation - Parsing (Run {run_id})\n\n"
    report += "## Métriques Globales\n"
    report += f"- **Exact Match** : {metrics_summary.get('exact_match', 0.0):.2%}\n"
    report += f"- **Average F1-score** : {metrics_summary.get('avg_f1', 0.0):.2f}\n"
    
    report += "\n## Détail par bloc\n"
    for field, f1 in metrics_summary.get('field_f1s', {}).items():
        report += f"- `{field}` : {f1:.2f}\n"
        
    return report

def generate_retrieval_report(run_id: str, metrics_summary: dict) -> str:
    """
    Génère un rapport Markdown pour une expérience de Retrieval.
    """
    report = f"# Rapport d'Évaluation - Retrieval (Run {run_id})\n\n"
    report += "## Métriques Globales\n"
    report += f"- **Recall@1** : {metrics_summary.get('recall_at_1', 0.0):.2%}\n"
    report += f"- **Recall@5** : {metrics_summary.get('recall_at_5', 0.0):.2%}\n"
    report += f"- **MRR** : {metrics_summary.get('mrr', 0.0):.3f}\n"
    report += f"- **nDCG@5** : {metrics_summary.get('ndcg_at_5', 0.0):.3f}\n"
    
    return report
