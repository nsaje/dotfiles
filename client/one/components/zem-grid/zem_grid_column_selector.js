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
        templateUrl: '/components/zem-grid/templates/zem_grid_column_selector.html',
        controller: [function () {
            var vm = this;

            vm.categories = [];
            vm.columnChecked = columnChecked;

            init();

            function init () {
                initCategories();
                vm.api.onColumnsLoaded(null, function () {
                    initCategories();
                });
            }

            function columnChecked (column) {
                vm.api.setVisibleColumns(column, column.visible);
            }

            function initCategories () {
                // Place columns in a corresponding category
                // If column is un-selectable (always visible) or not shown skip it
                var columns = vm.api.getColumns();
                vm.categories = [];
                vm.api.getMetaData().categories.forEach(function (category) {
                    var categoryColumns = columns.filter(function (column) {
                        var inCategory = category.fields.indexOf(column.field) !== -1;
                        return  inCategory && column.data.shown && !column.data.unselectable;
                    });

                    if (categoryColumns.length > 0) {
                        vm.categories.push({
                            'name': category.name,
                            'columns': categoryColumns,
                        });
                    }
                });
            }
        }],
    };
}]);
