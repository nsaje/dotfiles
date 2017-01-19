/* global angular, constants */

angular.module('one.widgets').component('zemGridBulkActions', {
    bindings: {
        api: '=',
    },
    templateUrl: '/app/widgets/zem-grid-integration/shared/bulk-actions/zemGridBulkActions.component.html',
    controller: function (zemGridConstants, zemGridBulkActionsService) { // eslint-disable-line max-len
        // TODO: alert, update daily stats

        var $ctrl = this;
        var service;

        $ctrl.actions = []; // Defined in $onInit
        $ctrl.isEnabled = isEnabled;
        $ctrl.execute = execute;


        $ctrl.$onInit = function () {
            service = zemGridBulkActionsService.createInstance($ctrl.api);
            service.setSelectionConfig();
            $ctrl.actions = service.getActions();
        };

        function isEnabled () {
            var selection = $ctrl.api.getSelection();
            if (selection.type === zemGridConstants.gridSelectionFilterType.NONE) {
                if (selection.selected.length == 1 && selection.selected[0].level == 0) {
                    return false;
                }
                return selection.selected.length > 0;
            }
            return true;
        }

        function execute (actionValue) {
            var selection = $ctrl.api.getSelection();
            var action = getActionByValue(actionValue);

            var convertedSelection = {};
            convertedSelection.selectedIds = selection.selected.filter(function (row) {
                return row.level == 1;
            }).map(function (row) {
                return row.id;
            });
            convertedSelection.unselectedIds = selection.unselected.filter(function (row) {
                return row.level == 1;
            }).map(function (row) {
                return row.id;
            });
            convertedSelection.filterAll = selection.type === zemGridConstants.gridSelectionFilterType.ALL;
            convertedSelection.filterId = selection.type === zemGridConstants.gridSelectionFilterType.CUSTOM ?
                selection.filter.batch.id : null;

            action.execute(convertedSelection);
        }

        function getActionByValue (value) {
            return $ctrl.actions.filter(function (action) {
                return action.value === value;
            })[0];
        }
    }
});
