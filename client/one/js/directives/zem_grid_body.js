/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridBody', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            rows: '=',
        },
        template: '' +
        '<tbody>' +
        '<zem-grid-row ng-repeat="row in ctrl.rows track by $index" ng-if="row.visible"' +
            'row="row",' +
            'options="ctrl.options",' +
        '/>' +
        '<tbody/>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
