/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellPerformanceIndicator', ['zemGridConstants', function (zemGridConstants) {

    var statusIcons = {},
        statusClasses = {};
    statusIcons[constants.emoticon.HAPPY] = 'happy_face.svg';
    statusClasses[constants.emoticon.HAPPY] = 'img-icon-happy';
    statusIcons[constants.emoticon.SAD] = 'sad_face.svg';
    statusClasses[constants.emoticon.SAD] = 'img-icon-sad';
    statusIcons[constants.emoticon.NEUTRAL] = 'neutral_face.svg';
    statusClasses[constants.emoticon.NEUTRAL] = 'img-icon-neutral';

    function isFieldVisible (rowLevel) {
        return rowLevel === zemGridConstants.gridRowLevel.BASE;
    }

    function getOverallIcon (overall) {
        if (overall) {
            return {
                file: statusIcons[overall],
                class: statusClasses[overall],
            };
        }
    }

    function getStatusList (statuses) {
        if (!statuses) {
            return [];
        }

        var statusList = [];
        statuses.forEach(function (status) {
            statusList.push({
                file: statusIcons[status.emoticon],
                class: statusClasses[status.emoticon],
                text: status.text,
            });
        });
        return statusList;
    }

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            row: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_performance_indicator.html',
        controller: ['$scope', 'config', function ($scope, config) {
            var vm = this;

            vm.config = config;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update () {
                vm.isFieldVisible = false;
                vm.overall = {
                    file: statusIcons[constants.emoticon.NEUTRAL],
                    class: statusClasses[constants.emoticon.NEUTRAL],
                };
                vm.statusList = [];

                if (vm.row) {
                    vm.isFieldVisible = isFieldVisible(vm.row.level);
                }

                if (vm.data) {
                    vm.overall = getOverallIcon(vm.data.overall);
                    vm.statusList = getStatusList(vm.data.list);
                }
            }
        }],
    };
}]);
