import xml.etree.ElementTree as ET


class CoverageParser:
    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()

    def get_total_metrics(self):
        return {
            "line_rate": float(self.root.attrib.get('line-rate', 0)) * 100,
            "branch_rate": float(self.root.attrib.get('branch-rate', 0)) * 100
        }

    def get_all_classes(self):

        for cls_node in self.root.findall('.//class'):
            yield cls_node

    def parse_class_data(self, cls_node):

        return {
            'name': cls_node.attrib['name'],
            'coverage': round(float(cls_node.attrib.get('line-rate', 0)) * 100, 1),
            'uncovered': [
                int(l.attrib['number'])
                for ls in cls_node.findall('lines')
                for l in ls.findall('line')
                if l.attrib.get('hits') == '0'
            ]
        }