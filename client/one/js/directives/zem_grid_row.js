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
        '<tr>' +
            '<zem-grid-cell ng-repeat="col in ctrl.row.data.stats track by $index"' +
                'options="ctrl.options"' +
                'cell="col"'+
            '/>' +
        '<tr/>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
