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
            '<div class="zem-grid-body">' +
                '<zem-grid-row ng-repeat="row in rows track by $index" ng-if="row.visible" ' +
                    'row="row" ' +
                    'options="ctrl.options" ' +
                '></zem-grid-row>' +
            '</div>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
