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
        link: function (scope, tElement) {
            // Prevent closing of dropdown-menu when checkbox is clicked.
            $(tElement).on('click', function (e) {
                e.stopPropagation();
            });
        },
        controller: ['zemGridStorageService', function (zemGridStorageService) {
            var vm = this;

            vm.categories = [];
            vm.columnChecked = columnChecked;

            init();

            function init () {
                initCategories();
            }

            function columnChecked () {
                zemGridStorageService.saveColumns(vm.grid);
                vm.grid.header.columns = vm.grid.meta.data.columns.filter(function (column) {
                    return column.shown && column.checked;
                });
                vm.grid.meta.pubsub.notify(vm.grid.meta.pubsub.EVENTS.DATA_UPDATED);
            }

            function initCategories () {
                // Place columns in a corresponding category
                // If column is un-selectable (always visible) or not shown skip it
                vm.categories = [];
                vm.grid.meta.data.categories.forEach(function (cat) {
                    var cols = vm.grid.meta.data.columns.filter(function (col) {
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
