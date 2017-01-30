angular.module('one.widgets').component('zemChart', {
    bindings: {
        level: '<',
        breakdown: '<',
        entityId: '<',
        gridApi: '<', // Used for selection - TODO: replace with SelectionService
    },
    templateUrl: '/app/widgets/zem-chart/zemChart.component.html',
    controller: function ($scope, $window, config, zemDataFilterService, zemChartService, zemChartObject, zemChartStorageService, zemChartMetricsService, zemGridConstants, zemNavigationNewService) { //eslint-disable-line max-len
        var $ctrl = this;
        var selectionListenerInitialized = false;

        $ctrl.onMetricsChanged = onMetricsChanged;
        $ctrl.removeLegendItem = removeLegendItem;

        $ctrl.$onInit = function () {
            var entity = zemNavigationNewService.getActiveEntity();
            if (entity || $ctrl.level === constants.level.ALL_ACCOUNTS) {
                initialize();
            } else {
                var handler = zemNavigationNewService.onActiveEntityChange(function () {
                    initialize();
                    handler();
                });
            }
        };

        function initialize () {
            $ctrl.config = config;

            // Initialize Chart Data Object and Service
            $ctrl.chart = zemChartObject.createChart();
            $ctrl.chartDataService = zemChartService.createDataService(
                $ctrl.chart, $ctrl.level, $ctrl.breakdown, $ctrl.entityId);
            $ctrl.chartDataService.initialize();

            initializeWindowResizeListeners();
            initializeDataListeners();

            loadMetrics();
            loadData();
        }


        function initializeDataListeners () {
            var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(loadData);
            var dataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(loadData);
            $scope.$on('$destroy', function () {
                dateRangeUpdateHandler();
                dataFilterUpdateHandler();
            });
        }

        function updateDataSource () {
            var metrics = [$ctrl.metrics.metric1.value];
            if ($ctrl.metrics.metric2) metrics.push($ctrl.metrics.metric2.value);
            $ctrl.chartDataService.setMetrics(metrics);
            $ctrl.chartDataService.setSelection(getSelection());
        }

        function loadData () {
            updateDataSource();
            $ctrl.chartDataService.getData().then(function () {
                // Chart is already updated
            });
        }

        function initializeWindowResizeListeners () {
            var w = angular.element($window);
            w.bind('resize', updateSize);
            $scope.$on('$destroy', function () {
                w.unbind('resize', updateSize);
            });

            function updateSize () {
                var chart = $('.chart').highcharts();

                var w = $('.chart').parent().width(),
                    h = $('.chart').height();
                // setsize will trigger the graph redraw
                if (chart && $('.graph-container').css('display') !== 'none') {
                    chart.setSize(w, h, false);
                }
            }
        }

        function removeLegendItem (item) { // eslint-disable-line no-unused-vars
            // TODO: Remove item using selection service
        }

        $ctrl.$onChanges = function () {
            // TODO: Use SelectionService and not directly GridApi
            if (!selectionListenerInitialized && $ctrl.gridApi) {
                $ctrl.gridApi.onSelectionUpdated($scope, loadData);
                selectionListenerInitialized = true;
            }
        };

        function getSelection () {
            // TODO: Use SelectionService
            if (!$ctrl.gridApi) return {};
            var gridSelection = $ctrl.gridApi.getSelection();
            var selection = {};
            selection.selectedIds = gridSelection.selected.filter(function (row) {
                return row.level === 1;
            }).map(function (row) {
                return row.id;
            });
            selection.unselectedIds = gridSelection.unselected.filter(function (row) {
                return row.level === 1;
            }).map(function (row) {
                return row.id;
            });
            selection.selectAll = gridSelection.type === zemGridConstants.gridSelectionFilterType.ALL;
            return selection;
        }


        // /////////////////////////////////////////////////////////////////
        // Metrics selection
        //
        function onMetricsChanged (metric1, metric2) {
            $ctrl.metrics.metric1 = metric1;
            $ctrl.metrics.metric2 = metric2;
            saveMetrics();
            loadData();
        }

        function saveMetrics () {
            zemChartStorageService.saveMetrics(
                {
                    metric1: $ctrl.metrics.metric1.value,
                    metric2: $ctrl.metrics.metric2 ? $ctrl.metrics.metric2.value : null
                }, $ctrl.level
            );
        }

        function loadMetrics () {
            var categories = $ctrl.chart.metrics.options;
            $ctrl.metrics = {
                metric1: zemChartMetricsService.findMetricByValue(categories, constants.chartMetric.CLICKS),
                metric2: zemChartMetricsService.findMetricByValue(categories, constants.chartMetric.IMPRESSIONS),
            };

            var metrics = zemChartStorageService.loadMetrics($ctrl.level);
            if (metrics) {
                var metric1 = zemChartMetricsService.findMetricByValue(categories, metrics.metric1);
                var metric2 = zemChartMetricsService.findMetricByValue(categories, metrics.metric2);

                if (metric1) $ctrl.metrics.metric1 = metric1;
                if (metric2) $ctrl.metrics.metric2 = metric2;
            }
        }
    }
});
