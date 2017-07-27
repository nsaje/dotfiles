angular.module('one.widgets').directive('zemGridCellActions', function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            row: '=',
            grid: '=',
        },
        template: require('./zemGridCellActions.component.html'),
        controller: function ($scope, zemGridConstants, zemGridStateAndStatusHelpers, zemGridActionsService, zemToastsService) { // eslint-disable-line max-len
            var vm = this;
            vm.isSaveRequestInProgress = vm.grid.meta.dataService.isSaveRequestInProgress;
            vm.stateValues = zemGridStateAndStatusHelpers
                .getStateValues(vm.grid.meta.data.level, vm.grid.meta.data.breakdown);
            vm.toggleState = toggleState;
            vm.execute = execute;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.row.data.archived', update);

            function update () {
                vm.showLoader = false;
                vm.active = false;
                vm.isEditable = false;
                vm.enablingAutopilotSourcesAllowed = true;
                vm.showStateSwitch = false;
                vm.buttons = [];

                if (vm.row) {
                    vm.enablingAutopilotSourcesAllowed = vm.row.inGroup ||
                        vm.grid.meta.data.ext.enablingAutopilotSourcesAllowed;
                    vm.isFieldVisible = isFieldVisible(vm.row.level);
                    vm.isRowArchived = vm.row.data.archived;
                    vm.showStateSwitch = zemGridActionsService.isStateSwitchVisible(
                        vm.grid.meta.data.level,
                        vm.grid.meta.data.breakdown,
                        vm.row
                    );

                    var buttons = zemGridActionsService.getButtons(
                        vm.grid.meta.data.level,
                        vm.grid.meta.data.breakdown,
                        vm.row
                    );
                    if (buttons.length > 0 && vm.grid.meta.data.breakdown !== constants.breakdown.PUBLISHER) {
                        vm.mainButton = buttons[0];
                        vm.buttons = buttons.slice(1);
                    } else {
                        vm.buttons = buttons;
                    }

                    if (vm.row.data.stats.state) {
                        var stateData = vm.row.data.stats.state;
                        vm.active = isActive(stateData.value);
                        vm.isEditable = stateData.isEditable;
                        vm.disabledMessage = stateData.editMessage;
                    }
                }
            }

            function execute (button) {
                vm.showLoader = true;
                button.action(vm.row, vm.grid, button).then(function () {
                    vm.showLoader = false;
                });
                if (button !== vm.mainButton) {
                    vm.modal.close();
                }
            }

            function toggleState () {
                if (!vm.isEditable || !vm.active && !vm.enablingAutopilotSourcesAllowed) {
                    return;
                }

                var state = vm.active ? vm.stateValues.paused : vm.stateValues.enabled;

                vm.showLoader = true;
                vm.grid.meta.dataService.saveData(state, vm.row, {data: {field: 'state'}})
                    .then(function () {
                        update();
                    })
                    .catch(function (data) {
                        if (data.state) {
                            zemToastsService.error(data.state);
                        } else {
                            zemToastsService.error(data.data.message);
                        }
                    })
                    .finally(function () {
                        vm.showLoader = false;
                    });
            }

            function isActive (state) {
                return state === vm.stateValues.enabled;
            }

            function isFieldVisible (rowLevel) {
                return rowLevel === zemGridConstants.gridRowLevel.BASE;
            }
        },
    };
});
