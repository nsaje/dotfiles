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
            '<div class="zem-grid-row" ng-class="getRowClass()">' +
                '<zem-grid-cell ng-repeat="col in row.data.stats track by $index" ' +
                    'cell="col" ' +
                    'options="options" ' +
                '></zem-grid-cell>' +
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
