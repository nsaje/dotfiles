require('./zemReportColumnSelector.component.less');

angular.module('one.widgets').component('zemReportColumnSelector', {
    bindings: {
        api: '=',
        disabled: '<',
        toggleColumns: '&',
    },
    template: require('./zemReportColumnSelector.component.html'),
    controller: function($element, $timeout, zemCostModeService) {
        var clonedColumns; // Cloned because report column selector must not change selected columns in grid

        var $ctrl = this;

        $ctrl.categories = [];
        $ctrl.onSelectColumn = onSelectColumn;
        $ctrl.onToggleColumns = onToggleColumns;

        $ctrl.$onInit = function() {
            init();
            $ctrl.api.onColumnsUpdated(null, init);
        };

        function onToggleColumns(newColumnsState) {
            setVisibleColumns(
                $ctrl.api.getTogglableColumns(clonedColumns),
                newColumnsState
            );
        }

        function onSelectColumn(selectedColumnField) {
            var column =
                $ctrl.api.findColumnInCategories(
                    $ctrl.categories,
                    selectedColumnField
                ) || {};
            setVisibleColumns(column, !column.visible, clonedColumns);
        }

        function setVisibleColumns(toggledColumns, visible, allColumns) {
            // Update columns visibility in clonedColumns
            var columnsToToggle = $ctrl.api.getColumnsToToggle(
                toggledColumns,
                allColumns
            );
            columnsToToggle.forEach(function(column) {
                column.visible = visible;
            });

            // Reinitialize $ctrl.categories with updated clonedColumns
            $ctrl.categories = $ctrl.api.getCategorizedColumns(
                zemCostModeService,
                clonedColumns
            );

            $ctrl.toggleColumns({
                columnsToToggle: columnsToToggle.map(getColumnName),
                visible: visible,
            });
        }

        function getColumnName(column) {
            return column.data.name;
        }

        function init() {
            clonedColumns = angular.copy($ctrl.api.getColumns());
            $ctrl.categories = $ctrl.api.getCategorizedColumns(
                zemCostModeService,
                clonedColumns
            );
        }
    },
});
