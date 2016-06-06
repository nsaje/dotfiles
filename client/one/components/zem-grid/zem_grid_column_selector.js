/* global oneApp */
'use strict';

oneApp.directive('zemGridColumnSelector', [function () {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_column_selector.html',
        controller: ['zemGridStorageService', 'zemGridApiService', function (zemGridStorageService, zemGridApiService) {
            var vm = this;

            vm.columns = vm.grid.meta.data.columns;
            vm.categories = [];
            vm.columnChecked = columnChecked;

            init();

            function init () {
                initCategories();
            }

            function columnChecked () {
                zemGridStorageService.saveColumns(vm.grid);
                var selectedColumns = vm.columns.filter(function (column) {
                    return column.shown && column.checked;
                });
                zemGridApiService.setSelectedColumns(vm.grid, selectedColumns);
            }

            function initCategories () {
                // Place columns in a corresponding category
                // If column is un-selectable (always visible) or not shown skip it
                vm.categories = [];
                vm.grid.meta.data.categories.forEach(function (cat) {
                    var cols = vm.columns.filter(function (col) {
                        return cat.fields.indexOf(col.field) !== -1 && col.shown && !col.unselectable;
                    });

                    if (cols.length > 0) {
                        vm.categories.push({
                            'name': cat.name,
                            'columns': cols,
                        });
                    }
                });
            }
        }],
    };
}]);
