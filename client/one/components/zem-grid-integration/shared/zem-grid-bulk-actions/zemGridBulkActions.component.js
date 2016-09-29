/* global angular, constants */
'use strict';

angular.module('one.legacy').directive('zemGridBulkActions', ['$window', 'api', function () {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            api: '=',
        },
        templateUrl: '/components/zem-grid-integration/shared/zem-grid-bulk-actions/zemGridBulkActions.component.html',
        controller: 'zemGridBulkActionsCtrl',
    };
}]);

angular.module('one.legacy').controller('zemGridBulkActionsCtrl', ['zemGridConstants', 'zemGridBulkActionsService', function (zemGridConstants, zemGridBulkActionsService) { // eslint-disable-line max-len
    // TODO: alert, update daily stats

    var vm = this;

    vm.actions = []; // Defined below
    vm.isEnabled = isEnabled;
    vm.execute = execute;

    var service = zemGridBulkActionsService.createInstance(vm.api);

    initialize();

    function initialize () {
        service.setSelectionConfig();
    }

    function isEnabled () {
        var selection = vm.api.getSelection();
        if (selection.type === zemGridConstants.gridSelectionFilterType.NONE) {
            if (selection.selected.length == 1 && selection.selected[0].level == 0) {
                return false;
            }
            return selection.selected.length > 0;
        }
        return true;
    }

    function execute (actionValue) {
        var metaData = vm.api.getMetaData();
        var selection = vm.api.getSelection();
        var action = getActionByValue(actionValue);

        var convertedSelection = {};
        convertedSelection.id = metaData.id;
        convertedSelection.selectedIds = selection.selected.map(function (row) {
            return row.data.stats.id.value;
        });
        convertedSelection.unselectedIds = selection.unselected.map(function (row) {
            return row.data.stats.id.value;
        });
        convertedSelection.filterAll = selection.type === zemGridConstants.gridSelectionFilterType.ALL;
        convertedSelection.filterId = selection.type === zemGridConstants.gridSelectionFilterType.CUSTOM ?
            selection.filter.batch.id : null;

        action.execute(convertedSelection);
    }

    vm.actions = service.getActions();

    function getActionByValue (value) {
        return vm.actions.filter(function (action) {
            return action.value === value;
        })[0];
    }
}]);
