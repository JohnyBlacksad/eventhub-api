"""Парсер отчётов покрытия coverage.xml.

Модуль содержит класс CoverageParser для извлечения метрик покрытия
из XML отчётов pytest-cov.

Используется в allurerc.mjs и quality_gate.py для анализа покрытия.
"""

import xml.etree.ElementTree as ET


class CoverageParser:
    """Парсер XML отчётов coverage.xml.

    Извлекает метрики покрытия (line_rate, branch_rate) и данные
    по классам/файлам.

    Attributes:
        tree: XML дерево отчёта.
        root: Корневой элемент XML.
    """

    def __init__(self, xml_path):
        """Инициализировать парсер с XML файлом.

        Args:
            xml_path: Путь к файлу coverage.xml.
        """
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()

    def get_total_metrics(self):
        """Получить общие метрики покрытия.

        Returns:
            dict: Словарь с line_rate и branch_rate в процентах.
        """
        return {
            "line_rate": float(self.root.attrib.get("line-rate", 0)) * 100,
            "branch_rate": float(self.root.attrib.get("branch-rate", 0)) * 100,
        }

    def get_all_classes(self):
        """Итератор по всем классам в отчёте.

        Yields:
            xml.Element: Элемент класса из XML.
        """
        for cls_node in self.root.findall(".//class"):
            yield cls_node

    def parse_class_data(self, cls_node):
        """Извлечь данные о покрытии класса.

        Args:
            cls_node: XML элемент класса.

        Returns:
            dict: Словарь с name, coverage %, и uncovered строками.
        """
        return {
            "name": cls_node.attrib["name"],
            "coverage": round(float(cls_node.attrib.get("line-rate", 0)) * 100, 1),
            "uncovered": [
                int(l.attrib["number"])
                for ls in cls_node.findall("lines")
                for l in ls.findall("line")
                if l.attrib.get("hits") == "0"
            ],
        }

    def get_file_coverage(self):
        file_stats = {}

        for cls_node in self.get_all_classes():
            file_name = cls_node.attrib.get("filename")
            if not file_name:
                continue

            file_name = file_name.split("eventhub-api/")[-1]

            total = 0
            covered = 0

            for line in cls_node.findall(".//line"):
                total += 1
                if int(line.attrib.get("hits", 0)) > 0:
                    covered += 1

            if total == 0:
                continue

            if file_name not in file_stats:
                file_stats[file_name] = {"total": 0, "covered": 0}

            file_stats[file_name]["total"] += total
            file_stats[file_name]["covered"] += covered

        result = []

        for filename, stats in file_stats.items():
            result.append({"name": filename, "covered": stats["covered"], "total": stats["total"]})

        return result
