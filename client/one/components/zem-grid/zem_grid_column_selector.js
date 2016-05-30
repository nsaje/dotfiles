/*global $,oneApp,constants*/
'use strict';

oneApp.directive('zemGridColumnSelector', ['config', function (config) {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid-columns-selector/zem_grid_columns_selector.html',
        compile: function compile (tElement) {
            // Prevent closing of dropdown-menu when checkbox is clicked.
            $(tElement).on('click', function (e) {
                e.stopPropagation();
            });

            return {
                pre: function preLink (scope, iElement, iAttrs, controller) {
                    return;
                },
                post: function postLink (scope, iElement, iAttrs, controller) {
                    return;
                }
            };
        },
        controller: ['$scope', '$element', '$attrs', 'zemGridStorageService', function ($scope, $element, $attrs, zemGridStorageService) { // eslint-disable-line max-len
            var vm = this;

            this.columns = [];
            this.categoryColumns = [];
            this.hasCategories = false;
            this.constants = constants;

            this.columnChecked = columnChecked;

            init();

            function init () {
                zemGridStorageService.loadColumns(vm.grid);
                initCategories();
                updateHeaderColumns();
            }

            function columnChecked(column) {
                zemGridStorageService.saveColumns(vm.grid);
                updateHeaderColumns();
            }

            function updateHeaderColumns () {
                vm.grid.header.columns = vm.grid.header.data.columns.filter(function (column) {
                    return column.shown && column.checked;
                });
                vm.grid.meta.pubsub.notify(vm.grid.meta.pubsub.EVENTS.DATA_UPDATED);
            }

            function initCategories () {
                vm.columns = vm.grid.header.data.columns.filter(function (column) {
                    return !column.unselectable;
                });

                var categoryColumns = [],
                    hasCategories = false;

                for (var i = 0; i < vm.grid.header.data.categories.length; i++) {
                    var cat = vm.grid.header.data.categories[i];

                    var cols = vm.columns.filter(function (col) {
                        return cat.fields.indexOf(col.field) !== -1 && col.shown && !col.unselectable;
                    });

                    if (cols.length > 0) {
                        categoryColumns.push({
                            'columns': cols,
                            'name': cat.name,
                        });
                        hasCategories = true;
                    }
                }
                vm.categoryColumns = categoryColumns;
                vm.hasCategories = hasCategories;
            }
        }],
    };
}]);
