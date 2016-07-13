/* global oneApp */
'use strict';

oneApp.directive('zemGridBreakdownSelector', [function () {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            api: '=',
        },
        templateUrl: '/components/zem-grid-actions/templates/zem_grid_breakdown_selector.html',
        controller: [function () {
            var vm = this;

            vm.onChecked = onChecked;
            vm.applyBreakdown = applyBreakdown;

            init();

            function init () {
                // Skip base level breakdown selection
                vm.breakdownGroups = vm.api.getMetaData().breakdownGroups.slice(1);
            }

            function onChecked (breakdown, group) {
                if (breakdown.checked) {
                    group.breakdowns.forEach(function (b) {
                        if (b !== breakdown) b.checked = false;
                    });
                }

                applyBreakdown();
            }

            function applyBreakdown () {
                // Add base level breakdown and all checked
                // breakdowns in successive levels
                var breakdown = [];
                var baseLevelGroup = vm.api.getMetaData().breakdownGroups[0];
                breakdown.push(baseLevelGroup.breakdowns[0]);
                vm.breakdownGroups.forEach(function (group) {
                    group.breakdowns.forEach(function (b) {
                        if (b.checked) breakdown.push(b);
                    });
                });
                vm.api.getDataService().setBreakdown(breakdown, true);
            }
        }],
    };
}]);
