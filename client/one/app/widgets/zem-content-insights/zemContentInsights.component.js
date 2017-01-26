/* globals angular,$ */
'use strict';

angular.module('one.widgets').component('zemContentInsights', {
    bindings: {
        entity: '<'
    },
    templateUrl: '/app/widgets/zem-content-insights/zemContentInsights.component.html',
    controller: function ($scope, $element, $window, $timeout, zemNavigationNewService, zemContentInsightsEndpoint) {
        var $ctrl = this;

        $ctrl.loading = true;
        $ctrl.expanded = true;

        $ctrl.$onChanges = function () {
            loadData();
        };

        function loadData () {
            if (!$ctrl.entity) return;

            zemContentInsightsEndpoint.getData($ctrl.entity).then (function (data) {
                $ctrl.data = data;
                $ctrl.loading = false;
                updateTableState();
            });
        }

        function updateTableState () {
            if (!$ctrl.data) return;
            // table can be either expanded(best and worst performers displayed side-by-side)
            // or shortened (only one table shown(best performer elements) with data bound
            // either to best or worst performers)
            var containerWidth = $('.zem-content-insights').width();

            if (containerWidth < 800) {
                $ctrl.expanded = false;
            } else {
                // when tab
                $ctrl.expanded = true;
            }
            $ctrl.showBestPerformersCollapsed();
        }

        $ctrl.showBestPerformersCollapsed = function () {
            $ctrl.collapsedDataState = 'best-performers';
            $ctrl.collapsedRows = $ctrl.data.bestPerformerRows;
        };

        $ctrl.showWorstPerformersCollapsed = function () {
            $ctrl.collapsedDataState = 'worst-performers';
            $ctrl.collapsedRows = $ctrl.data.worstPerformerRows;
        };

        var resize = function () {
            $scope.$watch(function () {
                return w.innerWidth();
            }, function () {
                updateTableState();
            }, true);
            $scope.$digest();
        };

        var w = angular.element($window);
        w.bind('resize', resize);
        $scope.$on('$destroy', function () {
            w.unbind('resize', resize);
        });
    }
});
