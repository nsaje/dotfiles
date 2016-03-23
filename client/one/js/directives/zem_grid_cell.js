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
            cell: '=',
        },
        template: '<td>{{cell}}<td/>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
