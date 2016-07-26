/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellExternalLink', ['zemGridEndpointColumns', function (zemGridEndpointColumns) {

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
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_external_link.html',
        controller: ['$scope', '$window', 'config', 'zemGridConstants', function ($scope, $window, config, zemGridConstants) { // eslint-disable-line max-len
            var vm = this;
            vm.config = config;
            vm.openUrl = openUrl;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update () {
                vm.fieldVisible = isFieldVisible();
                vm.text = null;
                vm.title = null;
                vm.url = null;
                vm.redirectorUrl = null;

                if (!vm.fieldVisible) {
                    return;
                }

                if (vm.data) {
                    vm.text = vm.data.text;

                    if (vm.data.url) {
                        vm.url = vm.data.url;
                        vm.redirectorUrl = vm.data.url;
                    }

                    if (vm.data.redirectorUrl) {
                        vm.redirectorUrl = vm.data.redirectorUrl;
                    }
                }
            }

            function isFieldVisible () {
                if (!vm.row || !vm.column) {
                    return false;
                }
                return !(vm.row.level === zemGridConstants.gridRowLevel.FOOTER && vm.column.data.totalRow === false);
            }

            function openUrl ($event) {
                $event.stopPropagation();
                $event.preventDefault();
                $window.open(vm.redirectorUrl || vm.url, '_blank');
            }
        }],
    };
}]);
