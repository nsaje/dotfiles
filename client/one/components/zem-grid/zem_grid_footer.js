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
            $scope.$on('dataLoaded', function () {
                var columns = $('.zem-grid-table .zem-grid-row:first-child .zem-grid-cell');
                var footerColumns = $('.zem-grid-footer .zem-grid-cell');
                columns.each(function (index, column) {
                    footerColumns[index].style.width = column.offsetWidth + 'px';
                });
            });
        }],
    };
}]);
