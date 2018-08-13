require('./zemChart.component.less');

angular.module('one.widgets').component('zemChart', {
    bindings: {
        level: '<',
        breakdown: '<',
        entityId: '<',
    },
    template: require('./zemChart.component.html'),
    controller: function(
        $scope,
        $window,
        config,
        zemDataFilterService,
        zemChartService,
        zemChartObject,
        zemChartStorageService,
        zemChartMetricsService,
        zemGridConstants,
        zemNavigationNewService,
        zemSelectionService,
        zemCostModeService
    ) {
        //eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.initialized = false;
        $ctrl.onMetricsChanged = onMetricsChanged;
        $ctrl.removeLegendItem = removeLegendItem;
        $ctrl.metricOptions = [];

        $ctrl.$onInit = function() {
            var entity = zemNavigationNewService.getActiveEntity();
            if (entity || $ctrl.level === constants.level.ALL_ACCOUNTS) {
                initialize();
            } else {
                var handler = zemNavigationNewService.onActiveEntityChange(
                    function() {
                        initialize();
                        handler();
                    }
                );
            }
        };

        $ctrl.$onChanges = function(changes) {
            if (changes.breakdown) {
                // If breakdown changes we need to replace chartDataService
                // It is not needed to refresh data immediately, therefor
                // new one is created when data refresh is requested
                $ctrl.chartDataService = null;
            }
        };

        function initialize() {
            $ctrl.config = config;

            // Initialize Chart Data Object and Service
            $ctrl.chart = zemChartObject.createChart();
            $ctrl.chartDataService = zemChartService.createDataService(
                $ctrl.chart,
                $ctrl.level,
                $ctrl.breakdown,
                $ctrl.entityId
            );
            $ctrl.chartDataService.initialize();

            subscribeToEvents();
            loadMetrics(true); // Initially use placeholder fallback for dynamic metrics
            loadData();
        }

        function subscribeToEvents() {
            var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(
                loadData
            );
            var dataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(
                loadData
            );

            var oldSelection = zemSelectionService.getSelection();
            var selectionUpdateHandler = zemSelectionService.onSelectionUpdate(
                function() {
                    if (
                        angular.equals(
                            oldSelection,
                            zemSelectionService.getSelection()
                        )
                    )
                        return;
                    oldSelection = zemSelectionService.getSelection();
                    loadData();
                }
            );

            $scope.$on('$destroy', function() {
                dateRangeUpdateHandler();
                dataFilterUpdateHandler();
                selectionUpdateHandler();
            });

            zemCostModeService.onCostModeUpdate(onCostModeChanged);
        }

        function updateDataSource() {
            if (!$ctrl.chartDataService) {
                $ctrl.chartDataService = zemChartService.createDataService(
                    $ctrl.chart,
                    $ctrl.level,
                    $ctrl.breakdown,
                    $ctrl.entityId
                );
            }

            var metrics = [$ctrl.metrics.metric1.value];
            if ($ctrl.metrics.metric2.value)
                metrics.push($ctrl.metrics.metric2.value);

            $ctrl.chartDataService.setMetrics(metrics);
            $ctrl.chartDataService.setSelection(getSelection());
        }

        function loadData() {
            updateDataSource();

            // FIXME: chartDataService can become null (proper reinitialization needed on breakdown change)
            var chartDataService = $ctrl.chartDataService;

            $ctrl.chartDataService.getData().then(function() {
                if (!$ctrl.initialized) {
                    // First request
                    $ctrl.initialized = true;

                    // Update Dynamic metrics - re-fetch if metrics are not available anymore (use default metrics)
                    loadMetrics();
                    var metrics = chartDataService.getMetrics();
                    if (
                        metrics[0] !== $ctrl.metrics.metric1.value ||
                        metrics[1] !== $ctrl.metrics.metric2.value
                    ) {
                        loadData();
                    }
                }
            });
        }

        function removeLegendItem(item) {
            if (!item.removable) return;

            switch (item.id) {
                case 'totals':
                    return zemSelectionService.unselectTotals();
                case 'selected':
                    return zemSelectionService.unselectAll();
                default:
                    return zemSelectionService.remove(item.id);
            }
        }

        function getSelection() {
            var selection = {};
            selection.selectedIds = zemSelectionService.getSelection().selected;
            selection.unselectedIds = zemSelectionService.getSelection().unselected;
            selection.totals = zemSelectionService.isTotalsSelected();
            selection.selectAll = zemSelectionService.isAllSelected();
            selection.batchId = zemSelectionService.getSelectedBatch();
            return selection;
        }

        // /////////////////////////////////////////////////////////////////
        // Metrics selection
        //
        function onCostModeChanged() {
            var costMode = zemCostModeService.getCostMode();

            if (!zemCostModeService.isTogglableCostMode(costMode)) return;

            var oppositeMetric;
            var changed = false;
            var oppositeCostMode = zemCostModeService.getOppositeCostMode(
                costMode
            );

            if (
                $ctrl.metrics.metric1 &&
                $ctrl.metrics.metric1.costMode === oppositeCostMode
            ) {
                oppositeMetric = zemChartMetricsService.findMetricByCostMode(
                    $ctrl.chart.metrics.options,
                    $ctrl.metrics.metric1.value,
                    costMode
                );

                $ctrl.metrics.metric1 = getMetric(oppositeMetric.value);
                changed = true;
            }

            if (
                $ctrl.metrics.metric2 &&
                $ctrl.metrics.metric2.costMode === oppositeCostMode
            ) {
                oppositeMetric = zemChartMetricsService.findMetricByCostMode(
                    $ctrl.chart.metrics.options,
                    $ctrl.metrics.metric2.value,
                    costMode
                );

                $ctrl.metrics.metric2 = getMetric(oppositeMetric.value);
                changed = true;
            }

            if (changed) {
                saveMetrics();
                loadData();
            }
        }

        function onMetricsChanged(metric1, metric2) {
            $ctrl.metrics.metric1 = metric1
                ? metric1
                : zemChartMetricsService.createEmptyMetric();
            $ctrl.metrics.metric2 = metric2
                ? metric2
                : zemChartMetricsService.createEmptyMetric();
            saveMetrics();
            loadData();
        }

        function saveMetrics() {
            zemChartStorageService.saveMetrics(
                {
                    metric1: $ctrl.metrics.metric1.value,
                    metric2: $ctrl.metrics.metric2
                        ? $ctrl.metrics.metric2.value
                        : null,
                },
                $ctrl.level
            );
        }

        function loadMetrics(usePlaceholderFallback) {
            var categories = $ctrl.chart.metrics.options;
            $ctrl.metrics = {
                metric1: zemChartMetricsService.findMetricByValue(
                    categories,
                    zemChartMetricsService.METRICS.CLICKS.value
                ),
                metric2: zemChartMetricsService.findMetricByValue(
                    categories,
                    zemChartMetricsService.METRICS.IMPRESSIONS.value
                ),
            };

            var metrics = zemChartStorageService.loadMetrics($ctrl.level);
            if (metrics) {
                $ctrl.metrics.metric1 = getMetric(
                    metrics.metric1,
                    usePlaceholderFallback
                );
                $ctrl.metrics.metric2 = getMetric(
                    metrics.metric2,
                    usePlaceholderFallback
                );
            }
        }

        function getMetric(metricValue, usePlaceholderFallback) {
            var metric = zemChartMetricsService.findMetricByValue(
                $ctrl.chart.metrics.options,
                metricValue
            );
            if (metric) {
                return metric;
            } else if (metricValue && usePlaceholderFallback) {
                return zemChartMetricsService.createPlaceholderMetric(
                    metricValue
                );
            }

            return zemChartMetricsService.createEmptyMetric();
        }
    },
});
