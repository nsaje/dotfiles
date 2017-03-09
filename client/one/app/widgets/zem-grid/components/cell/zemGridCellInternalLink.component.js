/* globals angular, constants */
'use strict';

angular.module('one.widgets').directive('zemGridCellInternalLink', function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            row: '=',
            column: '=',
            grid: '=',
        },
        templateUrl: '/app/widgets/zem-grid/components/cell/zemGridCellInternalLink.component.html',
        controller: function ($scope, zemNavigationNewService) {
            var vm = this;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update () {
                vm.href = null;
                if (vm.data && vm.row.data && vm.row.entity) {
                    vm.href = zemNavigationNewService.getEntityHref(vm.row.entity);
                }
            }
        },
    };
});
