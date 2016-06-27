/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellPerformanceIndicator', ['config', function (config) {

    var statusIcons = {},
        statusClasses = {};
    statusIcons[constants.emoticon.HAPPY] = 'happy_face.svg';
    statusClasses[constants.emoticon.HAPPY] = 'img-icon-happy';
    statusIcons[constants.emoticon.SAD] = 'sad_face.svg';
    statusClasses[constants.emoticon.SAD] = 'img-icon-sad';
    statusIcons[constants.emoticon.NEUTRAL] = 'neutral_face.svg';
    statusClasses[constants.emoticon.NEUTRAL] = 'img-icon-neutral';

    function isFieldVisible (rowLevel) {
        return rowLevel === 1;
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
        link: function (scope, element, attributes, ctrl) {
            ctrl.config = config;

            scope.$watch('ctrl.row', updateRow);
            scope.$watch('ctrl.data', updateRow);

            function updateRow () {
                ctrl.overall = {
                    file: statusIcons[constants.emoticon.NEUTRAL],
                    class: statusClasses[constants.emoticon.NEUTRAL],
                };

                if (ctrl.row) {
                    ctrl.isFieldVisible = isFieldVisible(ctrl.row.level);
                }

                if (ctrl.data) {
                    ctrl.overall = getOverallIcon(ctrl.data.overall);
                    ctrl.statusList = getStatusList(ctrl.data.list);
                }
            }
        },
        controller: [function () {}],
    };
}]);
