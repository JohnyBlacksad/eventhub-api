"""Применение меток Allure к тестам на основе pytest маркеров.

Модуль содержит класс AllureLabelApplier который:
- Собирает все маркеры с теста
- Извлекает метаданные (epic, feature, story, severity, suite, tags) из enum'ов
- Применяет метки динамически через allure.dynamic API

Использует BaseMarkerEnum для автоматической регистрации всех enum'ов с маркерами.
"""

import allure

from tests.core.const.base_enum_marker import BaseMarkerEnum


class AllureLabelApplier:
    SEVERITY_PRIORITY = {
        "blocker": 4,
        "critical": 3,
        "normal": 2,
        "minor": 1,
        "trivial": 0,
    }

    def __init__(self, default_owner: str = "ADMIN"):
        self.default_owner = default_owner
        self.enums = BaseMarkerEnum.get_all()

    def __get_contributions(self, mark_name):
        """
        Собирает вклад от всех енумов для данного маркера.
        Возвращает словарь с возможными ключам:
        epic, layer, feature, story, severities (список).
        """

        contributions = {}

        for enum_cls in self.enums:
            try:
                member = enum_cls[mark_name]
            except KeyError:
                continue

            if hasattr(member, "epic"):
                contributions["epic"] = member.epic
            if hasattr(member, "layer"):
                contributions["layer"] = member.layer
            if hasattr(member, "feature") and "feature" not in contributions:
                contributions["feature"] = member.feature
            if hasattr(member, "story") and "story" not in contributions:
                contributions["story"] = member.story
            if hasattr(member, "severity"):
                contributions.setdefault("severities", []).append(member.severity)

            # --- Новые атрибуты для suite ---
            if hasattr(member, "parent_suite") and "parent_suite" not in contributions:
                contributions["parent_suite"] = member.parent_suite
            if hasattr(member, "suite") and "suite" not in contributions:
                contributions["suite"] = member.suite
            if hasattr(member, "sub_suite") and "sub_suite" not in contributions:
                contributions["sub_suite"] = member.sub_suite

            # ← ТАГ ДОБАВЛЯЕМ из ЛЮБОГО енума у которого есть атрибут 'tag'
            if hasattr(member, 'tag'):
                contributions.setdefault('tags', []).append(member.tag)

        return contributions

    def __get_owner_from_marker(self, item):
        owner_marker = item.get_closest_marker("owner")
        if owner_marker and owner_marker.args:
            return owner_marker.args[0]
        return self.default_owner

    def _get_max_severity(self, severities):
        if not severities:
            return "normal"
        max_priority = -1
        selected = "normal"
        for sev in severities:
            priority = self.SEVERITY_PRIORITY.get(sev, -1)
            if priority > max_priority:
                max_priority = priority
                selected = sev
        return selected

    def _build_description(self, epic, feature, story, layer):
        parts = []
        if epic:
            parts.append(f"Epic: {epic}")
        if feature:
            parts.append(f"Feature: {feature}")
        if story:
            parts.append(f"Story: {story}")
        if layer:
            parts.append(f"Layer: {layer}")
        if parts:
            return " | ".join(parts)
        return "No description available"

    def apply(self, item):
        test_marks = {marker.name for marker in item.iter_markers()}

        all_contributions = {
            "epic": None,
            "layer": None,
            "feature": None,
            "story": None,
            "severities": [],
            "parent_suite": None,
            "suite": None,
            "sub_suite": None,
            'tags': [],
        }

        for mark_name in test_marks:
            contrib = self.__get_contributions(mark_name)

            if contrib.get("epic") and not all_contributions["epic"]:
                all_contributions["epic"] = contrib["epic"]
            if contrib.get("layer") and not all_contributions["layer"]:
                all_contributions["layer"] = contrib["layer"]
            if contrib.get("feature") and not all_contributions["feature"]:
                all_contributions["feature"] = contrib["feature"]
            if contrib.get("story") and not all_contributions["story"]:
                all_contributions["story"] = contrib["story"]
            if contrib.get("severities"):
                all_contributions["severities"].extend(contrib["severities"])

            # --- новые ---
            if contrib.get("parent_suite") and not all_contributions["parent_suite"]:
                all_contributions["parent_suite"] = contrib["parent_suite"]
            if contrib.get("suite") and not all_contributions["suite"]:
                all_contributions["suite"] = contrib["suite"]
            if contrib.get("sub_suite") and not all_contributions["sub_suite"]:
                all_contributions["sub_suite"] = contrib["sub_suite"]
            if contrib.get('tags'):
                all_contributions['tags'].extend(contrib['tags'])

        epic = all_contributions["epic"] or "Unknown Tests"
        layer = all_contributions["layer"] or "unknown"
        feature = all_contributions["feature"] or "General"
        story = all_contributions["story"] or "General Operations"
        severity = self._get_max_severity(all_contributions["severities"])
        description = self._build_description(epic, feature, story, layer)
        owner = self.__get_owner_from_marker(item)

        # Родительские suite-метки (берём из маркеров, если есть, иначе fallback)
        parent_suite = all_contributions["parent_suite"] or epic
        suite = all_contributions["suite"] or feature
        sub_suite = all_contributions.get("sub_suite")
        if sub_suite:
            allure.dynamic.sub_suite(sub_suite)

        allure.dynamic.epic(epic)
        allure.dynamic.feature(feature)
        allure.dynamic.story(story)

        # Устанавливаем лейблы для Suites
        allure.dynamic.parent_suite(parent_suite)
        allure.dynamic.suite(suite)

        allure.dynamic.label("test_layer", layer)
        allure.dynamic.severity(severity)
        allure.dynamic.description(description)
        allure.dynamic.label("owner", owner)

        # ← Добавляем теги из ВСЕХ енумов у которых есть атрибут 'tag'
        for tag_value in all_contributions['tags']:
            allure.dynamic.tag(tag_value)
