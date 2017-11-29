require('./zemGridColumnSelector.component.less');

angular.module('one.widgets').component('zemGridColumnSelector', {
    bindings: {
        api: '=',
    },
    template: require('./zemGridColumnSelector.component.html'),
    controller: function ($element, $timeout, zemCostModeService) {

        var $ctrl = this;

        $ctrl.categories = [];
        $ctrl.bareBoneCategories = [];
        $ctrl.filteredBareCategories = [];
        $ctrl.onSelectColumn = onSelectColumn;
        $ctrl.focusInput = focusInput;
        $ctrl.toggleColumns = toggleColumns;

        $ctrl.isCostModeToggleAllowed = zemCostModeService.isToggleAllowed;
        $ctrl.toggleCostMode = zemCostModeService.toggleCostMode;

        $ctrl.$onInit = function () {
            initializeCategories();
            $ctrl.api.onColumnsUpdated(null, initializeCategories);
        };

        function toggleColumns (isChecked) {
            $ctrl.bareBoneCategories.forEach(function (bareBoneCategory) {
                bareBoneCategory.columns.forEach(function (column) {
                    if (!column.disabled) {
                        column.visible = isChecked;
                    }
                });
            });
            $ctrl.filteredBareCategories = cloneObjects($ctrl.bareBoneCategories);

            var costMode = zemCostModeService.getCostMode();
            var columns = $ctrl.api.getColumns();
            var filteredCols = columns.filter(function (col) {
                if (col.disabled || !col.data.shown || col.data.permanent) return false;
                if (zemCostModeService.isTogglableCostMode(col.data.costMode)) {
                    return col.data.costMode === costMode;
                }
                return true;
            });
            $ctrl.api.setVisibleColumns(filteredCols, isChecked);
        }

        function focusInput ($event) {
            $event.stopPropagation();
            $timeout(function () {
                $element.find('#search-column').focus();
            }, 0);
        }

        function onSelectColumn (bareBoneColumn) {
            var temp = $ctrl.filteredBareCategories;
            var currColumn;

            $ctrl.categories.some(function (category) {
                currColumn = category.columns.find(function (column) {
                    return bareBoneColumn.field === column.field;
                });
                return currColumn;
            });

            if (currColumn) {
                currColumn.visible = bareBoneColumn.visible;
            }

            $ctrl.api.setVisibleColumns(currColumn, currColumn.visible);

            // this code is needed because #setVisibleColumns runs initializeCategories()
            $ctrl.filteredBareCategories = temp;
        }

        function cloneObjects (arr) {
            return arr.map(function (bareBoneCategory) {
                return angular.extend({}, bareBoneCategory);
            });
        }

        function initializeCategories () {
            $ctrl.categories = $ctrl.api.getCategorizedColumns(zemCostModeService);
            $ctrl.costModePlatform = zemCostModeService.getCostMode() === constants.costMode.PLATFORM;
            $ctrl.bareBoneCategories = $ctrl.api.getBareBoneCategories(zemCostModeService);
            $ctrl.filteredBareCategories = cloneObjects($ctrl.bareBoneCategories);
        }
    }
});
