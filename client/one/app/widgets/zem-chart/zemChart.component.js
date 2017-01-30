angular.module('one.widgets').component('zemChart', {
    bindings: {
        level: '<',
        breakdown: '<',
        entityId: '<',
        gridApi: '<', // Used for selection - TODO: replace with SelectionService
    },
    templateUrl: '/app/widgets/zem-chart/zemChart.component.html',
    controller: function ($scope, $window, config, zemDataFilterService, zemChartService, zemChartObject, zemChartStorageService, zemGridConstants) { //eslint-disable-line max-len
        var $ctrl = this;
        var selectionListenerInitialized = false;
        $ctrl.chartMetricUpdate = chartMetricUpdate;
        $ctrl.removeLegendItem = removeLegendItem;

        $ctrl.$onInit = function () {
            $ctrl.config = config;

            // Initialize Chart Data Object and Service
            $ctrl.chart = zemChartObject.createChart();
            $ctrl.chartDataService = zemChartService.createDataService(
                $ctrl.chart, $ctrl.level, $ctrl.breakdown, $ctrl.entityId);
            $ctrl.chartDataService.initialize();

            // Metrics initialization
            loadMetrics();
            updateMetricOptions();

            initializeWindowResizeListeners();
            initializeDataListeners();
            loadData();
        };


        function initializeDataListeners () {
            var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(loadData);
            var dataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(loadData);
            $scope.$on('$destroy', function () {
                dateRangeUpdateHandler();
                dataFilterUpdateHandler();
            });
        }

        function updateDataSource () {
            $ctrl.chartDataService.setMetrics([$ctrl.metrics.metric1, $ctrl.metrics.metric2]);
            $ctrl.chartDataService.setSelection(getSelection());
        }

        function loadData () {
            updateDataSource();
            $ctrl.chartDataService.getData().then(function () {
                // Chart is already updated
                updateMetricOptions();
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

        function chartMetricUpdate () {
            saveMetrics();
            loadData();
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
        // Metrics selection Stuff TODO: Refactor - use dedicated components
        //
        function saveMetrics () {
            zemChartStorageService.saveMetrics(
                {metric1: $ctrl.metrics.metric1, metric2: $ctrl.metrics.metric2}, $ctrl.level
            );
        }

        function loadMetrics () {
            var metrics = zemChartStorageService.loadMetrics($ctrl.level);
            if (metrics) {
                $ctrl.metrics = metrics;
            } else {
                $ctrl.metrics = {metric1: constants.chartMetric.CLICKS, metric2: constants.chartMetric.IMPRESSIONS};
            }
        }


        function updateMetricOptions () {
            $ctrl.metric2Options = getMetric2Options($ctrl.chart.metrics.options);
        }

        function getMetric2Options (metricOptions) {
            // add (default) option to disable second metric
            return $.merge([{'value': 'none', 'name': 'None'}], metricOptions);
        }

        $ctrl.getSelectedName = function (selected) {
            // Returns the name of the selected item. ui-select doesn't update the name correctly when choices
            // change so the right name is returned here.
            if (!selected) {
                return '';
            }

            for (var i = 0; i < $ctrl.metric2Options.length; i++) {
                if ($ctrl.metric2Options[i].value === selected.value) {
                    return $ctrl.metric2Options[i].name;
                }
            }
            return '';
        };
    }
});
