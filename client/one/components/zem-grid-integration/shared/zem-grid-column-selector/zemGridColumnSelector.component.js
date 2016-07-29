/* global oneApp */
'use strict';

oneApp.directive('zemGridColumnSelector', [function () {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            api: '=',
        },
        templateUrl: '/components/zem-grid-integration/shared/zem-grid-column-selector/zemGridColumnSelector.component.html',
        controller: 'zemGridColumnSelectorCtrl',
    };
}]);


oneApp.controller('zemGridColumnSelectorCtrl', [function () {
    var MSG_DISABLED_COLUMN = 'Column is available when coresponding breakdown is visible.';

    var vm = this;

    vm.categories = [];
    vm.getTooltip = getTooltip;
    vm.columnChecked = columnChecked;

    initialize();

    function initialize () {
        initCategories();
        vm.api.onColumnsUpdated(null, initCategories);
    }

    function columnChecked (column) {
        vm.api.setVisibleColumns(column, column.visible);
    }

    function getTooltip (column) {
        if (column.disabled) {
            return MSG_DISABLED_COLUMN;
        }
        return null;
    }

    function initCategories () {
        // Place columns in a corresponding category
        // If column is un-selectable (always visible) or not shown skip it
        var columns = vm.api.getColumns();
        vm.categories = [];
        vm.api.getMetaData().categories.forEach(function (category) {
            var categoryColumns = columns.filter(function (column) {
                var inCategory = category.fields.indexOf(column.field) !== -1;
                return inCategory && column.data.shown && !column.data.permanent;
            });

            if (categoryColumns.length > 0) {
                vm.categories.push({
                    'name': category.name,
                    'columns': categoryColumns,
                });
            }
        });
    }
}]);
