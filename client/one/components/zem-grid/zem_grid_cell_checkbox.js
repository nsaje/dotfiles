/* globals oneApp */
'use strict';

oneApp.directive('zemGridCellCheckbox', [function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            col: '=',
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_checkbox.html',
        controller: ['$scope', 'zemGridConstants', function ($scope, zemGridConstants) {
            var vm = this;
            var pubsub = this.grid.meta.pubsub;

            vm.checkboxModel = {};
            vm.toggleSelection = toggleSelection;

            initialize();

            function initialize () {
                updateModel();
                pubsub.register(pubsub.EVENTS.EXT_SELECTION_UPDATED, updateModel);
                $scope.$watch('ctrl.row', updateModel);
            }

            function updateModel () {
                vm.checkboxModel.visible = isVisible();
                if (vm.checkboxModel.visible) {
                    vm.checkboxModel.checked = isChecked();
                    vm.checkboxModel.disabled = isDisabled();
                }
            }

            function isVisible () {
                if (!vm.row) return false;
                return vm.grid.meta.options.selection.levels.indexOf(vm.row.level) >= 0;
            }

            function isChecked () {
                var selection = vm.grid.ext.selection;
                var isFiltered = selection.filter.callback(vm.row);
                if (isFiltered) {
                    return selection.unselected.indexOf(vm.row) < 0;
                }
                return selection.selected.indexOf(vm.row) >= 0;
            }

            function isDisabled () {
                var maxSelected = vm.grid.meta.options.selection.maxSelected;
                var selection = vm.grid.ext.selection;
                if (maxSelected && selection.selected.length >= maxSelected) {
                    return !vm.checkboxModel.checked;
                }
                return false;
            }

            function toggleSelection () {
                var idx;
                var selection = vm.grid.ext.selection;
                var isFiltered = selection.filter.callback(vm.row);

                // If item is filtered its selection would be persisted in unselected collection
                // since it will actually be unselected by user. If not filtered selected collection
                // is used.
                var collection = isFiltered ? selection.unselected : selection.selected;
                idx = collection.indexOf(vm.row);
                if (idx >= 0) {
                    collection.splice(idx, 1);
                } else {
                    collection.push(vm.row);
                }

                pubsub.notify(pubsub.EVENTS.EXT_SELECTION_UPDATED, vm.grid.ext.selection);
            }
        }],
    };
}]);
