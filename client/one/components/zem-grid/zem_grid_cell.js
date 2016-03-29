/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridCell', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            cell: '=',
        },
        template: '' +
        '<div class="zem-grid-cell">' +
            '<span ng-if="$index===0 && row.data.breakdown && row.level>0">' +
                '<a ng-click="toggleCollapse(row)" class="action">' +
                '{{row.collapsed ? "[ + ]" : "[ - ]"}} ' +
                '</a>' +
            '</span>' +
            '<span>{{ctrl.cell}}</span>' +
        '</div>',
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
