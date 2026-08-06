"""
Generate thesis-ready evaluation reports for the clean shared-context experiment.

Outputs:
1. results/reports/model_comparison.xlsx
2. results/reports/SONUCLAR.md
3. results/reports/METODOLOJI.md
"""

import json
from pathlib import Path
from datetime import datetime

from _bootstrap import bootstrap_paths

bootstrap_paths()

from config import (
    ALL_MODELS,
    GENERATOR_MODELS,
    JUDGE_MODEL,
    METRICS,
    RESULTS_PATH,
    REPORTS_PATH,
)

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    print("Note: openpyxl not installed. Install it to export Excel reports.")


METRIC_KEYS = [
    "question_quality",
    "answer_correctness",
    "distractor_quality",
    "answer_relevancy",
]


def validate_result_payload(model_id: str, payload: dict) -> list[str]:
    """Return a list of validation issues for a result payload."""
    issues = []
    metadata = payload.get("metadata", {})
    comparison = payload.get("model_comparison", {})
    total_questions = metadata.get("total_questions")

    if metadata.get("generator_model") != model_id:
        issues.append("metadata.generator_model does not match expected model id")
    if metadata.get("generation_path") != "shared_contexts+production_mcq_generator":
        issues.append("generation_path is not the clean shared-context pipeline")
    if not metadata.get("shared_context_file"):
        issues.append("shared_context_file is missing")
    if not isinstance(total_questions, int) or total_questions <= 0:
        issues.append("total_questions is missing or invalid")

    for metric in METRIC_KEYS:
        metric_data = comparison.get(metric)
        if not metric_data:
            issues.append(f"{metric} metric is missing")
            continue
        if metric_data.get("mean") is None:
            issues.append(f"{metric} mean score is missing")
        if metric_data.get("count") != total_questions:
            issues.append(
                f"{metric} count ({metric_data.get('count')}) does not match total_questions ({total_questions})"
            )

    return issues


def load_all_results(results_dir: Path) -> dict:
    """Load all evaluation result files."""
    results = {}
    invalid_files = []
    for file in results_dir.glob("eval_*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
        model_id = data.get("metadata", {}).get("generator_model", file.stem)
        issues = validate_result_payload(model_id, data)
        if issues:
            invalid_files.append(f"{file.name}: " + "; ".join(issues[:4]))
            continue
        results[model_id] = data

    missing_models = [model for model in ALL_MODELS if model not in results]
    if missing_models or invalid_files:
        details = []
        if missing_models:
            details.append(
                "Missing evaluation results for models: " + ", ".join(missing_models)
            )
        if invalid_files:
            details.append(
                "Invalid evaluation files: " + " | ".join(invalid_files)
            )

        generated_candidates = []
        for model in ALL_MODELS:
            safe_name = model.replace("/", "-")
            generated_file = RESULTS_PATH.parent / "generated" / f"{safe_name}.json"
            if generated_file.exists():
                generated_candidates.append(generated_file.name)

        if generated_candidates:
            details.append(
                "Generated question files already exist: " + ", ".join(generated_candidates)
            )
            details.append(
                "Next step: run `python scripts/run_evaluation.py --condition all --force` "
                "with a Python environment that has the evaluation dependencies installed."
            )

        raise RuntimeError(
            "Report generation aborted: " + " ".join(details)
        )

    return results


def compute_overall_score(result: dict) -> float:
    """Average the four main metrics."""
    comparison = result.get("model_comparison", {})
    values = [(comparison.get(metric, {}).get("mean", 0) or 0) for metric in METRIC_KEYS]
    return sum(values) / len(METRIC_KEYS)


def sorted_results(results: dict) -> list[tuple[str, dict]]:
    """Sort models by overall score descending."""
    return sorted(results.items(), key=lambda item: compute_overall_score(item[1]), reverse=True)


def metric_leaders(results: dict) -> list[tuple[str, str, float]]:
    """Return the best-performing model for each metric."""
    leaders = []
    for metric in METRIC_KEYS:
        winner_id, winner_result = max(
            results.items(),
            key=lambda item: item[1].get("model_comparison", {}).get(metric, {}).get("mean", -1),
        )
        winner_score = winner_result["model_comparison"][metric]["mean"]
        leaders.append((metric, winner_id, winner_score))
    return leaders


def extract_experiment_metadata(results: dict) -> dict:
    """Extract shared experiment metadata and check consistency."""
    ranked = sorted_results(results)
    first_meta = ranked[0][1].get("metadata", {}) if ranked else {}

    shared_context_files = {
        item[1].get("metadata", {}).get("shared_context_file")
        for item in ranked
    }
    generation_paths = {
        item[1].get("metadata", {}).get("generation_path")
        for item in ranked
    }
    total_question_counts = {
        item[1].get("metadata", {}).get("total_questions")
        for item in ranked
    }

    if len(shared_context_files) > 1:
        raise RuntimeError(
            "Report generation aborted: models do not reference the same shared context file."
        )

    if generation_paths != {"shared_contexts+production_mcq_generator"}:
        raise RuntimeError(
            "Report generation aborted: one or more result files were not produced by the clean shared-context pipeline."
        )

    if len(total_question_counts) > 1:
        raise RuntimeError(
            "Report generation aborted: models were not evaluated on the same number of questions."
        )

    return {
        "shared_context_file": first_meta.get("shared_context_file", "unknown"),
        "shared_context_metadata": first_meta.get("shared_context_metadata", {}),
        "judge_name": first_meta.get("judge_name", JUDGE_MODEL["name"]),
        "judge_model": first_meta.get("judge_model", JUDGE_MODEL["id"]),
        "generation_path": first_meta.get("generation_path", "unknown"),
        "evaluated_question_count": first_meta.get("total_questions", "unknown"),
    }


def generate_excel(results: dict, output_dir: Path) -> Path:
    """Generate Excel comparison table."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if not HAS_OPENPYXL:
        txt_file = output_dir / "model_comparison.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for rank, (model_id, result) in enumerate(sorted_results(results), start=1):
                f.write(
                    f"{rank}. {GENERATOR_MODELS.get(model_id, {}).get('name', model_id)} | "
                    f"Overall={compute_overall_score(result):.3f}\n"
                )
        return txt_file

    experiment = extract_experiment_metadata(results)
    shared_meta = experiment["shared_context_metadata"]
    ranked = sorted_results(results)

    wb = Workbook()
    ws = wb.active
    ws.title = "Model Comparison"

    header_font = Font(bold=True, size=12)
    title_font = Font(bold=True, size=14)
    center = Alignment(horizontal="center", vertical="center")
    thin = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    good_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    fair_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    weak_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

    ws["A1"] = "Quiz AI Tez Deneyi - Model Karsilastirma Sonuclari"
    ws["A1"].font = title_font
    ws.merge_cells("A1:J1")

    ws["A2"] = (
        f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"Hakem: {experiment['judge_name']} | "
        f"Degerlendirilen konu sayisi: {experiment['evaluated_question_count']}"
    )
    ws.merge_cells("A2:J2")

    ws["A3"] = (
        f"Yontem: Tek seferlik RAG -> donmus ortak baglam -> tum modeller -> kor LLM judge | "
        f"top_k={shared_meta.get('retrieval_top_k', 'n/a')} | "
        f"min_score={shared_meta.get('retrieval_min_score', 'n/a')}"
    )
    ws.merge_cells("A3:J3")

    headers = [
        "Sira",
        "Model",
        "Parametre",
        "N",
        "Soru Kalitesi",
        "Cevap Dogrulugu",
        "Secenek Kalitesi",
        "Cevap Ilgisi",
        "Genel",
        "Baglam Dosyasi",
    ]
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=5, column=col, value=header)
        cell.font = header_font
        cell.alignment = center
        cell.border = thin

    for row_idx, (model_id, result) in enumerate(ranked, start=6):
        meta = result.get("metadata", {})
        comparison = result.get("model_comparison", {})
        model_info = GENERATOR_MODELS.get(model_id, {})

        q = comparison.get("question_quality", {}).get("mean", 0) or 0
        a = comparison.get("answer_correctness", {}).get("mean", 0) or 0
        d = comparison.get("distractor_quality", {}).get("mean", 0) or 0
        r = comparison.get("answer_relevancy", {}).get("mean", 0) or 0
        overall = compute_overall_score(result)

        row = [
            row_idx - 5,
            model_info.get("name", model_id),
            model_info.get("params", "?"),
            meta.get("total_questions", 0),
            round(q, 3),
            round(a, 3),
            round(d, 3),
            round(r, 3),
            round(overall, 3),
            Path(meta.get("shared_context_file", "unknown")).name,
        ]

        for col_idx, value in enumerate(row, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = center
            cell.border = thin

            if 5 <= col_idx <= 9:
                if value >= 0.75:
                    cell.fill = good_fill
                elif value >= 0.60:
                    cell.fill = fair_fill
                else:
                    cell.fill = weak_fill

    widths = [8, 24, 14, 8, 15, 16, 17, 14, 10, 22]
    for idx, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(idx)].width = width

    ws2 = wb.create_sheet("Methodology")
    ws2["A1"] = "Temel metodoloji"
    ws2["A1"].font = title_font
    methodology_lines = [
        "1. 100 konu basligi topics.json dosyasindan alinmistir.",
        "2. RAG retrieval tek sefer calistirilmistir.",
        "3. Ortak baglamlar shared_rag_contexts.json dosyasina dondurulmustur.",
        "4. Tum modeller ayni donmus baglam dosyasini kullanmistir.",
        "5. Uretim icin production MCQGenerator kullanilmistir.",
        f"6. Puanlama icin bagimsiz {experiment['judge_model']} hakem modeli kullanilmistir.",
    ]
    for idx, line in enumerate(methodology_lines, start=3):
        ws2[f"A{idx}"] = line

    ws3 = wb.create_sheet("Metric Leaders")
    ws3["A1"] = "Metrik Bazli Liderler"
    ws3["A1"].font = title_font
    ws3["A3"] = "Metrik"
    ws3["B3"] = "En Iyi Model"
    ws3["C3"] = "Skor"
    for cell in ("A3", "B3", "C3"):
        ws3[cell].font = header_font
        ws3[cell].border = thin
        ws3[cell].alignment = center

    for row_idx, (metric, model_id, score) in enumerate(metric_leaders(results), start=4):
        ws3.cell(row=row_idx, column=1, value=metric).border = thin
        ws3.cell(
            row=row_idx,
            column=2,
            value=GENERATOR_MODELS.get(model_id, {}).get("name", model_id),
        ).border = thin
        score_cell = ws3.cell(row=row_idx, column=3, value=round(score, 3))
        score_cell.border = thin
        score_cell.alignment = center

    output_file = output_dir / "model_comparison.xlsx"
    wb.save(output_file)
    return output_file


def generate_results_md(results: dict, output_dir: Path) -> Path:
    """Generate thesis-ready results markdown."""
    output_dir.mkdir(parents=True, exist_ok=True)
    experiment = extract_experiment_metadata(results)
    shared_meta = experiment["shared_context_metadata"]
    ranked = sorted_results(results)

    best_model_id, best_result = ranked[0]
    best_name = GENERATOR_MODELS.get(best_model_id, {}).get("name", best_model_id)
    best_overall = compute_overall_score(best_result)

    lines = [
        "# Deney Sonuclari",
        "",
        f"**Rapor Tarihi:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Hakem Model:** {experiment['judge_name']}",
        f"**Ortak Baglam Dosyasi:** `{Path(experiment['shared_context_file']).name}`",
        f"**Degerlendirilen Konu Sayisi:** {experiment['evaluated_question_count']}",
        f"**Retrieval Ayarlari:** top_k={shared_meta.get('retrieval_top_k', 'n/a')}, min_score={shared_meta.get('retrieval_min_score', 'n/a')}",
        "",
        "## 1. Ozet",
        "",
        "Bu deneyde 100 sabit bilim konusu icin RAG retrieval bir kez calistirilmis, elde edilen baglamlar dondurulmus ve tum uretici modeller ayni baglam dosyasi ile test edilmistir. Boylece gozlenen farklar retrieval farkindan degil, generator model farkindan kaynaklanmaktadir.",
        "",
        f"En yuksek genel skor **{best_name}** modeli tarafindan **{best_overall:.3f}** degeri ile elde edilmistir.",
        "",
        "## 2. Model Karsilastirma Tablosu",
        "",
        "| Sira | Model | Parametre | Soru Kalitesi | Cevap Dogrulugu | Secenek Kalitesi | Cevap Ilgisi | Genel |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]

    for rank, (model_id, result) in enumerate(ranked, start=1):
        comparison = result.get("model_comparison", {})
        model_info = GENERATOR_MODELS.get(model_id, {})
        q = comparison.get("question_quality", {}).get("mean", 0) or 0
        a = comparison.get("answer_correctness", {}).get("mean", 0) or 0
        d = comparison.get("distractor_quality", {}).get("mean", 0) or 0
        r = comparison.get("answer_relevancy", {}).get("mean", 0) or 0
        overall = compute_overall_score(result)

        lines.append(
            f"| {rank} | {model_info.get('name', model_id)} | {model_info.get('params', '?')} | "
            f"{q:.3f} | {a:.3f} | {d:.3f} | {r:.3f} | {overall:.3f} |"
        )

    lines.extend([
        "",
        "## 3. Metrik Bazli Liderler",
        "",
        "| Metrik | En Iyi Model | Skor |",
        "|---|---|---:|",
    ])

    for metric, model_id, score in metric_leaders(results):
        lines.append(
            f"| {metric} | {GENERATOR_MODELS.get(model_id, {}).get('name', model_id)} | {score:.3f} |"
        )

    lines.extend([
        "",
        "## 4. Genel Fark Analizi",
        "",
        "| Model | Genel Skor | En Iyi Modele Fark |",
        "|---|---:|---:|",
    ])

    for model_id, result in ranked:
        overall = compute_overall_score(result)
        delta = overall - best_overall
        lines.append(
            f"| {GENERATOR_MODELS.get(model_id, {}).get('name', model_id)} | {overall:.3f} | {delta:.3f} |"
        )

    lines.extend([
        "",
        "## 5. Yorum",
        "",
        "Bu tabloda tum modeller ayni donmus RAG baglamlarini kullandigi icin sonuclar dogrudan generator yetenegi karsilastirmasi olarak yorumlanabilir. Genel skor, dort ana metrigin esit agirlikli ortalamasi olarak hesaplanmistir.",
        "",
        "Secenek kalitesi metrigi tum modeller icin diger metriklere gore daha zorlayici bir alan olarak gozukmektedir. Bu durum, ikna edici fakat yanlis distractor uretiminin soru govdesi olusturmaktan daha zor olduguna isaret etmektedir.",
        "",
        "## 6. Gecerlilik Notu",
        "",
        "Bu rapor yalnizca `shared_contexts+production_mcq_generator` uretim yoluna sahip deney dosyalarindan uretilmistir. Dolayisiyla sonuclar, topic-only fallback veya model-bazli degisen retrieval akislarindan etkilenmemektedir.",
    ])

    output_file = output_dir / "SONUCLAR.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return output_file


def generate_methodology_md(results: dict, output_dir: Path) -> Path:
    """Generate methodology markdown for the clean experiment."""
    output_dir.mkdir(parents=True, exist_ok=True)
    experiment = extract_experiment_metadata(results)
    shared_meta = experiment["shared_context_metadata"]

    lines = [
        "# Metodoloji",
        "",
        "Bu deney duzeni, generator model farkini olcmek amaciyla retrieval varyansini sabitleyecek sekilde kurulmustur.",
        "",
        "## 1. Deney Tasarimi",
        "",
        "1. `topics.json` dosyasinda yer alan 100 insan-benzeri bilim konusu sabitlenmistir.",
        "2. Production retriever kullanilarak bu 100 konu icin RAG retrieval tek sefer calistirilmistir.",
        f"3. Retrieval ciktilari `{Path(experiment['shared_context_file']).name}` dosyasina dondurulmustur.",
        "4. Tum generator modeller yalnizca bu donmus baglam dosyasindan beslenmistir.",
        "5. Production MCQGenerator kullanilarak her model ayni baglamlardan soru uretmistir.",
        f"6. Uretilen sorular {experiment['judge_name']} ile kor bicimde puanlanmistir.",
        "",
        "## 2. Neden Bu Yontem Secilmistir?",
        "",
        "LLM model karsilastirmasi yapilirken retrieval tarafinin modelden modele degismesi metodolojik karisiklik yaratir. Bu nedenle retrieval bir kez yapilmis ve dondurulmustur. Boylece olculen farkin retrieval'dan degil modelden gelmesi saglanmistir.",
        "",
        "## 3. Retrieval Parametreleri",
        "",
        f"- top_k: {shared_meta.get('retrieval_top_k', 'n/a')}",
        f"- min_score: {shared_meta.get('retrieval_min_score', 'n/a')}",
        f"- degerlendirilen konu sayisi: {experiment['evaluated_question_count']}",
        "",
        "## 4. Degerlendirme Metrikleri",
        "",
        "| Metrik | Iyi Esik | Aciklama |",
        "|---|---:|---|",
    ]

    for key in METRIC_KEYS:
        metric = METRICS[key]
        lines.append(
            f"| {key} | {metric['good_threshold']:.2f} | {metric['description']} |"
        )

    lines.extend([
        "",
        "## 5. Raporlama ve Karsilastirma Kurali",
        "",
        "- Her model icin once metrik ortalamalari hesaplanir.",
        "- Genel skor, dort ana metrigin esit agirlikli ortalamasidir.",
        "- Raporlarda metrik bazli liderler ayrica verilir; boylece tek bir genel skora asiri bagimlilik azaltilir.",
        "- Sonuc dosyalari ancak tum metrikler tum sorular icin mevcutsa kabul edilir.",
        "",
        "## 6. Gecerlilik Kontrolleri",
        "",
        "- Tum modeller ayni konu listesi ile test edilmistir.",
        "- Tum modeller ayni donmus baglam dosyasini kullanmistir.",
        "- Uretim icin ayni production prompt/validator hatti kullanilmistir.",
        "- Hakem model generator ailesinden bagimsizdir.",
        "- Kor degerlendirme uygulanmistir; promptlara model adi dahil edilmemistir.",
    ])

    output_file = output_dir / "METODOLOJI.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return output_file


def main():
    print("=" * 60)
    print("RAPORLAR OLUSTURULUYOR")
    print("=" * 60)

    results = load_all_results(RESULTS_PATH)
    if not results:
        raise RuntimeError("No evaluation results found. Run the experiment first.")

    REPORTS_PATH.mkdir(parents=True, exist_ok=True)
    excel_file = generate_excel(results, REPORTS_PATH)
    results_md = generate_results_md(results, REPORTS_PATH)
    methodology_md = generate_methodology_md(results, REPORTS_PATH)

    print(f"Created: {excel_file}")
    print(f"Created: {results_md}")
    print(f"Created: {methodology_md}")


if __name__ == "__main__":
    main()
