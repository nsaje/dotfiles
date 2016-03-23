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
        '<thead>' +
            '<tr>' +
                '<th ng-repeat="col in header.columns">' +
                    '<span class="col-title">{{ col }}</span>' +
                '</th>' +
            '</tr>' +
        '<thead/>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
