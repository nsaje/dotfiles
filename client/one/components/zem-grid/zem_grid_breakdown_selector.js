/* global oneApp */
'use strict';

oneApp.directive('zemGridBreakdownSelector', [function () {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_breakdown_selector.html',
        controller: ['zemGridStorageService', function (zemGridStorageService) {
            var vm = this;

            vm.onChecked = onChecked;
            vm.applyBreakdown = applyBreakdown;

            init();

            function init () {
                // Skip base level breakdown selection
                vm.breakdownGroups = vm.grid.meta.data.breakdownGroups.slice(1);
            }

            function onChecked (breakdown, group) {
                if (breakdown.checked) {
                    group.breakdowns.forEach(function (b) {
                        if (b !== breakdown) b.checked = false;
                    });
                }
            }

            function applyBreakdown () {
                var selectedBreakdown = [];

                var baseLevelGroup = vm.grid.meta.data.breakdownGroups[0];
                selectedBreakdown.push(baseLevelGroup.breakdowns[0]);

                vm.breakdownGroups.forEach(function (group) {
                    group.breakdowns.forEach(function (b) {
                        if (b.checked) selectedBreakdown.push(b);
                    });
                });

                vm.grid.meta.source.selectedBreakdown = selectedBreakdown;
                vm.grid.meta.source.getData();
            };
        }],
    };
}]);
