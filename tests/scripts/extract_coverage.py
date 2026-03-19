#!/usr/bin/env python3
import json
import sys
from pathlib import Path

from tests.scripts.coverage_parser import CoverageParser

if __name__ == "__main__":
    xml_path = sys.argv[1] if len(sys.argv) > 1 else "./tests/reports/allure-results/coverage.xml"
    if not Path(xml_path).exists():
        print(json.dumps({"error": "Coverage file not found"}))
        sys.exit(1)

    parser = CoverageParser(xml_path)

    metrics = parser.get_total_metrics()
    classes_report = []
    for cls_node in parser.get_all_classes():
        data = parser.parse_class_data(cls_node)
        classes_report.append(data)

    result = {
        "total_coverage": round(metrics["line_rate"], 1),
        "branch_coverage": round(metrics["branch_rate"], 1),
        "packages": classes_report,
    }
    print(json.dumps(result, indent=2))

    file_coverage = parser.get_file_coverage()
    if file_coverage:
        results_dir = Path(xml_path).parent
        coverage_json_path = results_dir / "coverage.json"
        with open(coverage_json_path, "w") as f:
            json.dump(file_coverage, f, indent=2)
        print(f"Coverage data saved to {coverage_json_path}", file=sys.stderr)
