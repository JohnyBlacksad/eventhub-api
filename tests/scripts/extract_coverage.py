#!/usr/bin/env python3

import xml.etree.ElementTree as ET
import json
import sys
from pathlib import Path
from tests.scripts.coverage_parser import CoverageParser

def extract_coverage(xml_path: str) -> dict:
    """Извлечь метрики покрытия из XML"""

    parser = CoverageParser(xml_path)
    metrics = parser.get_total_metrics()

    classes_report = []
    for cls_node in parser.get_all_classes():
        data = parser.parse_class_data(cls_node)
        classes_report.append(data)

    return {
        'total_coverage': round(metrics['line_rate'], 1),
        'branch_coverage': round(metrics['branch_rate'], 1),
        'packages': classes_report
    }



if __name__ == "__main__":
    xml_path = sys.argv[1] if len(sys.argv) > 1 else './tests/reports/allure-results/coverage.xml'

    if not Path(xml_path).exists():
        print(json.dumps({'error': 'Coverage file not found'}))
        sys.exit(1)

    result = extract_coverage(xml_path)
    print(json.dumps(result, indent=2))