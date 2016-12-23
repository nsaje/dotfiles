angular.module('one.legacy').directive('zemGridCellEditButton', function () {
    var EDITABLE_ENTITIES = [
        constants.entityType.CONTENT_AD,
    ];

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            row: '=',
            column: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_edit_button.html',
        controller: function ($scope, zemGridConstants, zemGridStateAndStatusHelpers, zemUploadTriggerService, zemUploadApiConverter) { // eslint-disable-line max-len
            var vm = this;
            vm.editRow = editRow;

            function editRow () {
                if (!vm.row || !vm.isFieldVisible) {
                    return;
                }

                vm.grid.meta.dataService.editRow(vm.row).success(function (response) {
                    zemUploadTriggerService.openEditModal(
                        vm.grid.meta.data.id,
                        response.data.batch_id,
                        zemUploadApiConverter.convertCandidatesFromApi(response.data.candidates),
                        vm.grid.meta.api.loadData
                    );
                });
            }
        },
    };
});
