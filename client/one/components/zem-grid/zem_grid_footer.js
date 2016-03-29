/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridFooter', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            footer: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_footer.html',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
