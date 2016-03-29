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
            row: '=',
        },
        template: '' +
            '<div class="zem-grid-row" ng-class="getRowClass()" >' +
                '<zem-grid-cell ng-repeat="col in row.data.stats track by $index" ' +
                    'ng-if="row.type!=GridRowType.BREAKDOWN"' +
                    'cell="col" ' +
                    'options="options" ' +
                '></zem-grid-cell>' +
                '<div class="zem-grid-cell" ng-if="row.type==GridRowType.BREAKDOWN">' +
                    '<a ng-click="loadMore(row)">' +
                        '- {{row.data.pagination.size}} of {{row.data.pagination.count}} -' +
                    '</a>' +
                '</div>' +
                '<div class="zem-grid-cell" ng-if="row.type==GridRowType.BREAKDOWN">' +
                    '<a ng-click="loadMore(row, 5)"> (show 5 more) </a>' +
                '</div>' +
            '</div>',
        controller: ['$scope', function ($scope) {
            $scope.getRowClass = function () {
                var classes = [];
                classes.push('level-' + this.row.level);

                if (this.row.level === $scope.dataSource.breakdowns.length) {
                    classes.push('level-last');
                }
                return classes;
            };
        }],
    };
}]);
