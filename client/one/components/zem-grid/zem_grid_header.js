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
        templateUrl: '/components/zem-grid/templates/zem_grid_header.html',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
