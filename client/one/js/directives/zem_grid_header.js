/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridHeader', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            header: '=',
        },
        template: '' +
            '<div class="zem-grid-header">' +
                '<div class="zem-grid-cell" ng-repeat="col in header.columns">' +
                    '<span class="col-title">{{ col }}</span>' +
                '</div>' +
            '</div>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
