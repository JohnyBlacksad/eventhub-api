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
        severity: "normal",
        owner: "ADMIN",
        layer: "BACKEND"
    },

    plugins: {
        // awesome дашборд (группировка по epic/feature/story)
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
                        levels: ["blocker", "critical", "normal", "minor", "trivial"],
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
        "unit-tests": {
            import: "@allurereport/plugin-awesome",
            options: {
                reportName: "Unit Tests",
                groupBy: ["parentSuite", "suite", "subSuite"],
                // charts не указаны — будут использованы значения по умолчанию
                charts: [
                    {
                        type: "testResultSeverities",
                        title: "Серьёзность тестов" ,
                        levels: ["blocker", "critical", "normal", "minor", "trivial"],
                        statuses: ["passed", "failed", "broken", "skipped", "unknown"],
                        includeUnset: true
                    },
                    {
                        type: "testBaseGrowthDynamics",
                        title: "Динамика количества тестов",
                        statuses: ["passed", "failed", "broken", "skipped", "unknown"],
                        limit: 10
                    },
                    {
                        type: "stabilityDistribution",
                        title: "Стабильность по функционалу",
                        threshold: 90,
                        skipStatuses: ["skipped", "unknown"],
                        groupBy: "subSuite"
                    },
                    {
                        type: "durations",
                        title: "Длительность по сервисам",
                        groupBy: "subSuite"
                    },
                    {
                        type: "statusDynamics",
                        title: "Динамика статусов",
                        limit: 10, // последние 10 прогонов
                        statuses: ["passed", "failed", "broken", "skipped", "unknown"]
                    },
                    {
                        type: "statusTransitions",
                        title: "Flaky",
                        limit: 10
                    }
                ]
            }
        },

    },

    variables: {
        "Environment": "WSL2 / Ubuntu",
        "Python": "3.12",
        "Layer": "Backend",
        "Framework": "pytest + mongomock-motor",
        "Total Coverage": `${coverage.total_coverage}%`,
        "Branch Coverage": `${coverage.branch_coverage}%`,
        "Run Date": new Date().toLocaleString("ru-RU"),
        "Git Branch": process.env.CI_COMMIT_BRANCH || "local",
        "Commit": process.env.CI_COMMIT_SHA?.slice(0, 8) || "local"
    }
});