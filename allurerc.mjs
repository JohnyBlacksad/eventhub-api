import { defineConfig } from "allure";
import { execSync } from "child_process";
import fs from "fs";

// Извлечь покрытие из XML
function getCoverage() {
    try {
        const xmlPath = './tests/reports/allure-results/coverage.xml';

        if (!fs.existsSync(xmlPath)) {
            return {
                total_coverage: 0,
                branch_coverage: 0,
                packages: []
            };
        }

        const result = execSync(`PYTHONPATH=/home/artem/eventhub-api python3 tests/scripts/extract_coverage.py ${xmlPath}`, {
            encoding: 'utf8'
        });

        return JSON.parse(result);
    } catch (error) {
        console.error('Failed to extract coverage:', error.message);
        return {
            total_coverage: 0,
            branch_coverage: 0,
            packages: []
        };
    }
}

const coverage = getCoverage();

export default defineConfig({
    name: "EventHub API Dashboard",
    output: "./allure-report",
    historyPath: "./allure-history.jsonl",
    appendHistory: true,

    qualityGate: {
        rules: [
            {
                maxFailures: 0,
                fastFail: true
            }
        ]
    },

    defaultLabels: {
        severity: "NORMAL",
        owner: "ADMIN",
        layer: "BACKEND"
    },

    plugins: {
        // Твой существующий awesome (группировка по epic/feature/story)
        awesome: {
            options: {
                reportName: "EventHub API",
                reportLanguage: "ru",
                singleFile: false,
                groupBy: ["epic", "feature", "story"],
                charts: [
                    {
                        type: "currentStatus",
                        title: "Текущий статус",
                        statuses: ["passed", "failed", "broken", "skipped", "unknown"],
                        metric: "passed"
                    },
                    {
                        type: "statusDynamics",
                        title: "Динамика статусов",
                        limit: 10,
                        statuses: ["passed", "failed", "broken", "skipped", "unknown"]
                    },
                    {
                        type: "testResultSeverities",
                        title: "Серьёзность тестов",
                        levels: ["BLOCKER", "CRITICAL", "NORMAL", "MINOR", "TRIVIAL"],
                        statuses: ["passed", "failed", "broken", "skipped", "unknown"],
                        includeUnset: true
                    },
                    {
                        type: "durations",
                        title: "Время выполнения",
                        groupBy: "none"
                    },
                    {
                        type: "statusTransitions",
                        title: "Переходы статусов",
                        limit: 10
                    },
                    {
                        type: "testingPyramid",
                        title: "Тестовая пирамида",
                        layers: ["unit", "integration", "load"]
                    },
                    {
                        type: "stabilityDistribution",
                        title: "Стабильность по функционалу",
                        threshold: 90,
                        skipStatuses: ["skipped", "unknown"],
                        groupBy: "feature"
                    }
                ]
            }
        },

        // Твой dashboard
        dashboard: {
            options: {
                reportName: "Общая статистика",
                reportLanguage: "ru",
                singleFile: false,
                layout: [
                    {
                        type: "currentStatus",
                        title: "Общий статус"
                    },
                    {
                        type: "statusDynamics",
                        title: "Динамика за 10 запусков",
                        limit: 10
                    },
                    {
                        type: "testingPyramid",
                        title: "Тестовая пирамида",
                        layers: ["unit", "integration", "load"]
                    },
                    {
                        type: "durations",
                        title: "Время выполнения",
                        groupBy: "none"
                    }
                ]
            }
        },

        // Дополнительный отчёт с группировкой по parentSuite/suite/subSuite
        "suites-view": {
            import: "@allurereport/plugin-awesome",
            options: {
                reportName: "По сьютам (parentSuite → suite → subSuite)",
                groupBy: ["parentSuite", "suite", "subSuite"]
                // charts не указаны — будут использованы значения по умолчанию
            }
        },

        // Отчёт с группировкой epic → feature → sub_suite (если нужно)
        "deep-view": {
            import: "@allurereport/plugin-awesome",
            options: {
                reportName: "Глубинная иерархия (epic → feature → sub_suite)",
                groupBy: ["epic", "feature", "sub_suite"]
            }
        },

        // Отчёт только по story
        "story-view": {
            import: "@allurereport/plugin-awesome",
            options: {
                reportName: "По сториз",
                groupBy: ["story"]
            }
        }
    },

    variables: {
        "Environment": "WSL2 / Ubuntu",
        "Python": "3.12",
        "Layer": "BACKEND",
        "Framework": "pytest + mongomock-motor",
        "Total Coverage": `${coverage.total_coverage}%`,
        "Branch Coverage": `${coverage.branch_coverage}%`,
        "Run Date": new Date().toLocaleString("ru-RU"),
        "Git Branch": process.env.CI_COMMIT_BRANCH || "local",
        "Commit": process.env.CI_COMMIT_SHA?.slice(0, 8) || "local"
    }
});