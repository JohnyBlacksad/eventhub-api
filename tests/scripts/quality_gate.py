#!/usr/bin/env python3

import sys
from pathlib import Path

from tests.scripts.coverage_parser import CoverageParser

MIN_TOTAL_COVERAGE = 75.0
MIN_PACKAGE_COVERAGE = 50.0
REQUIRED_MODULES = [
    "app.services.auth",
    "app.services.user",
    "app.models.user",
]


def run_quality_gate(xml_path: str):
    if not Path(xml_path).exists():
        print(f"Error: File {xml_path} not found")
        sys.exit(1)

    parser = CoverageParser(xml_path)
    total_metrics = parser.get_total_metrics()
    total_cov = total_metrics["line_rate"]

    if total_cov < MIN_TOTAL_COVERAGE:
        print(f"FAIL: Total coverage {total_cov:.1f}% is below threshold {MIN_TOTAL_COVERAGE}%")
        sys.exit(1)

    failed_modules = []
    found_modules = {}
    for cls_node in parser.get_all_classes():
        data = parser.parse_class_data(cls_node)

        for req in REQUIRED_MODULES:
            if req in data["name"]:
                found_modules[req] = min(found_modules.get(req, 100), data["coverage"])

    for req in REQUIRED_MODULES:
        if req not in found_modules:
            failed_modules.append(f"   - {req}: NOT FOUND in report")
        elif found_modules[req] < MIN_PACKAGE_COVERAGE:
            failed_modules.append(f"   - {req}: {found_modules[req]:.1f}% < {MIN_PACKAGE_COVERAGE}%")

    if failed_modules:
        print("FAIL: Required modules quality check failed:")
        print("\n".join(failed_modules))
        sys.exit(1)

    print(f"PASS: Quality Gate passed with {total_cov:.1f}% total coverage")
    sys.exit(0)


if __name__ == "__main__":
    xml_path = sys.argv[1] if len(sys.argv) > 1 else "./tests/reports/allure-results/coverage.xml"
    run_quality_gate(xml_path)
