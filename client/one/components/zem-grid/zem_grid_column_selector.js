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
        controller: ['zemGridStorageService', 'zemGridApi', function (zemGridStorageService, zemGridApiService) {
            var vm = this;

            vm.categories = [];
            vm.columnChecked = columnChecked;

            init();

            function init () {
                initCategories();
            }

            function columnChecked (column) {
                vm.api.setVisibleColumns(column, column.visible);
            }

            function initCategories () {
                // Place columns in a corresponding category
                // If column is un-selectable (always visible) or not shown skip it
                var columns = vm.api.getColumns();
                vm.categories = [];
                vm.api.getMetaData().categories.forEach(function (cat) {
                    var categoryColumns = columns.filter(function (col) {
                        return cat.fields.indexOf(col.field) !== -1 && col.shown && !col.unselectable;
                    });

                    if (categoryColumns.length > 0) {
                        vm.categories.push({
                            'name': cat.name,
                            'columns': categoryColumns,
                        });
                    }
                });
            }
        }],
    };
}]);
