/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridRow', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            row: '=',
        },
        template: '' +
            '<div>' +
                '<zem-grid-cell ng-repeat="col in ctrl.row.data.stats track by $index"' +
                    'options="ctrl.options"' +
                    'cell="col"' +
                '/>' +
            '</div>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
