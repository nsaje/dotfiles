/* globals angular */
angular.module('one.legacy').component('zemGridColumnSelector', {
    bindings: {
        api: '=',
    },
    templateUrl: '/components/zem-grid-integration/shared/zem-grid-column-selector/zemGridColumnSelector.component.html',
    controller: function () {
        var MSG_DISABLED_COLUMN = 'Column is available when coresponding breakdown is visible.';

        var $ctrl = this;

        $ctrl.categories = [];
        $ctrl.getTooltip = getTooltip;
        $ctrl.columnChecked = columnChecked;

        $ctrl.$onInit = function () {
            initCategories();
            $ctrl.api.onColumnsUpdated(null, initCategories);
        };

        function columnChecked (column) {
            $ctrl.api.setVisibleColumns(column, column.visible);

            var columns = $ctrl.api.getColumns();
            columns.forEach(function (col) {
                if (col.data.hasOwnProperty('autoSelect') && col.data.autoSelect === column.field) {
                    $ctrl.api.setVisibleColumns(col, column.visible);
                }
            });
        }

        function getTooltip (column) {
            if (column.disabled) {
                return MSG_DISABLED_COLUMN;
            }
            return null;
        }

        function getCategoryColumns (category, columns) {
            return columns.filter(function (column) {
                var inCategory = category.fields.indexOf(column.field) !== -1;
                return inCategory && column.data.shown && !column.data.permanent;
            });
        }

        function getCategory (category, columns) {
            var categoryColumns = getCategoryColumns(category, columns),
                subcategories = [];

            if (category.hasOwnProperty('subcategories')) {
                subcategories = category.subcategories.map(function (subcategory) {
                    return getCategory(subcategory, columns);
                });
            }

            return {
                name: category.name,
                description: category.description,
                type: category.type,
                subcategories: subcategories,
                columns: categoryColumns,
            };
        }

        function initCategories () {
            // Place columns in a corresponding category
            // If column is un-selectable (always visible) or not shown skip it
            var columns = $ctrl.api.getColumns();
            $ctrl.categories = [];
            $ctrl.api.getMetaData().categories.forEach(function (category) {
                var newCategory = getCategory(category, columns);
                if (newCategory.columns.length > 0 || newCategory.subcategories.length > 0) {
                    $ctrl.categories.push(newCategory);
                }
            });
        }
    }
});
