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
            $scope.$on('dataLoaded', function () {
                var columns = $('.zem-grid-table .zem-grid-row:first-child .zem-grid-cell');
                var headerColumns = $('.zem-grid-header .zem-grid-cell');
                var widthSum = 0;
                columns.each(function (index, column) {
                    headerColumns[index].style.width = column.offsetWidth + 'px';
                    widthSum += column.offsetWidth;
                });
                $('.zem-grid-body').width(widthSum);
                // $('.zem-grid-body').width($('.zem-grid-table').width());
            });
        }],
    };
}]);
