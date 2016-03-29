/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridCell', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            cell: '=',
        },
        template: '<div class="zem-grid-cell">{{ctrl.cell}}</div>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
