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
        template: '' +
            '<div class="zem-grid-footer">' +
                '<div class="zem-grid-cell" ng-repeat="col in footer.data.stats">' +
                    '<span class="col-title">{{ col }}</span>' +
                '</div>' +
            '</div>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
