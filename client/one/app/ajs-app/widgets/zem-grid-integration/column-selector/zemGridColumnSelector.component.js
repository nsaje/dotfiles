require('./zemGridColumnSelector.component.less');

angular.module('one.widgets').component('zemGridColumnSelector', {
    bindings: {
        api: '=',
    },
    template: require('./zemGridColumnSelector.component.html'),
    controller: function($element, $timeout, zemCostModeService) {
        var $ctrl = this;

        $ctrl.categories = [];
        $ctrl.onColumnToggled = onColumnToggled;
        $ctrl.onAllColumnsToggled = onAllColumnsToggled;
        $ctrl.focusInput = focusInput;
        $ctrl.isCostModeToggleAllowed = zemCostModeService.isToggleAllowed;
        $ctrl.toggleCostMode = zemCostModeService.toggleCostMode;

        $ctrl.$onInit = function() {
            initializeCategories();
            $ctrl.api.onColumnsUpdated(null, initializeCategories);
        };

        function onAllColumnsToggled(newColumnsState) {
            $ctrl.api.setVisibleColumns(
                $ctrl.api.getTogglableColumns($ctrl.api.getColumns()),
                newColumnsState
            );
        }

        function onColumnToggled(selectedColumnField) {
            var column = $ctrl.api.findColumnInCategories(
                $ctrl.categories,
                selectedColumnField
            );
            $ctrl.api.setVisibleColumns(
                column,
                !column.visible,
                $ctrl.api.getColumns()
            );
        }

        function focusInput($event) {
            $event.stopPropagation();
            $timeout(function() {
                $element.find('#search-column').focus();
            }, 0);
        }

        function initializeCategories() {
            $ctrl.categories = $ctrl.api.getCategorizedColumns(
                zemCostModeService,
                $ctrl.api.getColumns()
            );
            $ctrl.isCostModePlatform =
                zemCostModeService.getCostMode() ===
                constants.costMode.PLATFORM;
        }
    },
});
