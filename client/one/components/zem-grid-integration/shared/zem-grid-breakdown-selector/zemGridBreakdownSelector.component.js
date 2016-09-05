/* globals angular */
'use strict';

angular.module('one.legacy').directive('zemGridBreakdownSelector', [function () {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            api: '=',
        },
        templateUrl: '/components/zem-grid-integration/shared/zem-grid-breakdown-selector/zemGridBreakdownSelector.component.html',
        controller: 'zemGridBreakdownSelectorCtrl',
    };
}]);


angular.module('one.legacy').controller('zemGridBreakdownSelectorCtrl', [function () {
    var vm = this;

    vm.onChecked = onChecked;
    vm.applyBreakdown = applyBreakdown;

    initialize();

    function initialize () {
        // Skip base level breakdown selection
        vm.breakdownGroups = [
            vm.api.getMetaData().breakdownGroups.structure,
            vm.api.getMetaData().breakdownGroups.delivery,
            vm.api.getMetaData().breakdownGroups.time,
        ].filter (function (group) { return group.available !== false; });
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
        var baseLevelGroup = vm.api.getMetaData().breakdownGroups.base;
        breakdown.push(baseLevelGroup.breakdowns[0]);
        vm.breakdownGroups.forEach(function (group) {
            group.breakdowns.forEach(function (b) {
                if (b.checked) breakdown.push(b);
            });
        });
        vm.api.setBreakdown(breakdown, true);
    }
}]);
