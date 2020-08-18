angular
    .module('one.widgets')
    .directive('zemGridCellSubmissionStatus', function() {
        return {
            restrict: 'E',
            replace: true,
            scope: {},
            controllerAs: 'ctrl',
            bindToController: {
                data: '=',
                column: '=',
                row: '=',
                grid: '=',
            },
            template: require('./zemGridCellSubmissionStatus.component.html'),
            controller: function($scope, config, zemAuthStore) {
                var vm = this;
                vm.config = config;
                vm.hasPermission = zemAuthStore.hasPermission.bind(
                    zemAuthStore
                );
                vm.isPermissionInternal = zemAuthStore.isPermissionInternal.bind(
                    zemAuthStore
                );

                $scope.$watch('ctrl.row', update);
                $scope.$watch('ctrl.data', update);

                function update() {
                    vm.approved = null;
                    vm.nonApproved = null;
                    vm.noSubmissions = null;
                    vm.archived = null;

                    if (vm.row) {
                        vm.archived = vm.row.archived;
                    }

                    if (vm.data) {
                        var submissions =
                            vm.data instanceof Array ? vm.data : [];

                        vm.approved = submissions.filter(function(submission) {
                            return (
                                submission.status ===
                                constants.contentAdApprovalStatus.APPROVED
                            );
                        });

                        vm.nonApproved = submissions.filter(function(
                            submission
                        ) {
                            return (
                                submission.status !==
                                constants.contentAdApprovalStatus.APPROVED
                            );
                        });

                        vm.noSubmissions = submissions.length === 0;
                    }
                }
            },
        };
    });
