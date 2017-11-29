require('./zemReportColumnSelector.component.less');

angular.module('one.widgets').component('zemReportColumnSelector', {
    bindings: {
        api: '=',
        selectedColumn: '&',
        toggleColumns: '&',
    },
    template: require('./zemReportColumnSelector.component.html'),
    controller: function ($element, $timeout, zemCostModeService) {

        var $ctrl = this;

        $ctrl.categories = [];
        $ctrl.filteredBareCategories = [];
        $ctrl.bareBoneCategories = [];
        $ctrl.fieldNames = [];
        $ctrl.onSelectColumn = onSelectColumn;
        $ctrl.onToggleColumns = onToggleColumns;

        $ctrl.isCostModeToggleAllowed = zemCostModeService.isToggleAllowed;
        $ctrl.toggleCostMode = zemCostModeService.toggleCostMode;

        $ctrl.$onInit = function () {
            initializeCategories();
            $ctrl.api.onColumnsUpdated(null, initializeCategories);
        };

        function onToggleColumns (isChecked) {
            $ctrl.bareBoneCategories.forEach(function (bareBoneCategory) {
                bareBoneCategory.columns.forEach(function (column) {
                    if (!column.disabled) {
                        column.visible = isChecked;
                    }
                });
            });
            $ctrl.filteredBareCategories = cloneObjects($ctrl.bareBoneCategories);
            $ctrl.toggleColumns({data: {selectedColumns: $ctrl.fieldNames, isChecked: isChecked}});
        }

        function onSelectColumn (bareBoneColumn) {
            $ctrl.selectedColumn({column: {name: bareBoneColumn.name, checked: bareBoneColumn.visible}});
        }

        function cloneObjects (arr) {
            return arr.map(function (bareBoneCategory) {
                return angular.extend({}, bareBoneCategory);
            });
        }

        function getBareBoneFieldNames (zemCostModeService) {
            var fieldNames = [];
            $ctrl.api.getCategorizedColumns(zemCostModeService).forEach(function (category) {
                category.columns.forEach(function (column) {
                    var c = column;
                    fieldNames.push(c.data.name);
                });
            });
            return fieldNames;
        }

        function initializeCategories () {
            $ctrl.categories = $ctrl.api.getCategorizedColumns(zemCostModeService);
            $ctrl.costModePlatform = zemCostModeService.getCostMode() === constants.costMode.PLATFORM;
            $ctrl.bareBoneCategories = $ctrl.api.getBareBoneCategories(zemCostModeService);
            $ctrl.filteredBareCategories = cloneObjects($ctrl.bareBoneCategories);
            $ctrl.fieldNames = getBareBoneFieldNames(zemCostModeService);
        }
    }
});
