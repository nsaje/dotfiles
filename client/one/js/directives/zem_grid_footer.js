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
        '<tfoot>' +
            '<tr>' +
                '<th ng-repeat="col in footer.data.stats">' +
                    '<span class="col-title">{{ col }}</span>' +
                '</th>' +
            '</tr>' +
        '</tfoot>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
