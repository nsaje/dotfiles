angular.module('one.widgets').directive('zemGridCellEditButton', function() {
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
        template: require('./zemGridCellEditButton.component.html'),
        controller: function(
            $scope,
            zemGridConstants,
            zemUploadService,
            zemUploadApiConverter
        ) {
            // eslint-disable-line max-len
            var vm = this;
            vm.editRow = editRow;
            vm.isFieldVisible = false;

            $scope.$watch('ctrl.row', update);

            function update() {
                if (vm.row) {
                    vm.isFieldVisible = isFieldVisible(vm.row.level);
                }
            }

            function editRow() {
                vm.grid.meta.dataService
                    .editRow(vm.row)
                    .then(function(response) {
                        zemUploadService.openEditModal(
                            vm.grid.meta.data.id,
                            response.data.batch_id,
                            zemUploadApiConverter.convertCandidatesFromApi(
                                response.data.candidates
                            ),
                            vm.grid.meta.api.loadData
                        );
                    });
            }

            function isFieldVisible(rowLevel) {
                return rowLevel === zemGridConstants.gridRowLevel.BASE;
            }
        },
    };
});
