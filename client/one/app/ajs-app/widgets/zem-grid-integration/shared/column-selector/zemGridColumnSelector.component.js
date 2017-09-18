angular.module('one.widgets').component('zemGridColumnSelector', {
    bindings: {
        api: '=',
    },
    template: require('./zemGridColumnSelector.component.html'),
    controller: function ($element, zemCostModeService) {
        var MSG_DISABLED_COLUMN = 'Column is available when coresponding breakdown is visible.';

        var $ctrl = this;

        $ctrl.categories = [];
        $ctrl.getTooltip = getTooltip;
        $ctrl.columnChecked = columnChecked;
        $ctrl.onDropdownToggle = onDropdownToggle;

        $ctrl.isCostModeToggleAllowed = zemCostModeService.isToggleAllowed;
        $ctrl.toggleCostMode = zemCostModeService.toggleCostMode;

        $ctrl.$onInit = function () {
            initializeCategories();
            $ctrl.api.onColumnsUpdated(null, initializeCategories);
        };

        function onDropdownToggle () {
            var scrollContainer = $($element.find('.dropdown-menu__container')[0]),
                switcher = $element.find('#cost-mode-switcher');

            if (switcher.length > 0 && scrollContainer.scrollTop() === 0) {
                switcher = $(switcher[0]);
                var bottom = switcher.outerHeight(true);
                scrollContainer.scrollTop(bottom);
            }
        }

        function columnChecked (column) {
            $ctrl.api.setVisibleColumns(column, column.visible);

            var columns = $ctrl.api.getColumns();
            var costMode = zemCostModeService.getCostMode();

            columns.forEach(function (col) {
                if (col.data.hasOwnProperty('autoSelect') && col.data.autoSelect === column.field) {
                    if (zemCostModeService.isTogglableCostMode(col.data.costMode)) {
                        if (col.data.costMode === costMode) $ctrl.api.setVisibleColumns(col, column.visible);
                    } else {
                        $ctrl.api.setVisibleColumns(col, column.visible);
                    }
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
            var costMode = zemCostModeService.getCostMode();

            return columns.filter(function (column) {
                var inCategory = category.fields.indexOf(column.field) !== -1;
                if (!inCategory || !column.data.shown || column.data.permanent) return false;
                if (zemCostModeService.isTogglableCostMode(column.data.costMode)) {
                    return column.data.costMode === costMode;
                }
                return true;
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

        function initializeCategories () {
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
            $ctrl.costModePlatform = zemCostModeService.getCostMode() === constants.costMode.PLATFORM;
        }
    }
});
