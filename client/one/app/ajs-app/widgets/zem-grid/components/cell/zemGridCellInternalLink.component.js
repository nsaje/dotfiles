angular.module('one.widgets').directive('zemGridCellInternalLink', function() {
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
        template: require('./zemGridCellInternalLink.component.html'),
        controller: function($scope, zemNavigationNewService) {
            var vm = this;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update() {
                vm.href = null;
                if (vm.data && vm.row.data && vm.row.entity) {
                    var includeQueryParams = true;
                    vm.href = zemNavigationNewService.getEntityHref(
                        vm.row.entity,
                        includeQueryParams
                    );
                }
            }
        },
    };
});
