angular
    .module('one.widgets')
    .directive('zemGridCellInternalLink', function(NgRouter, NgZone) {
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
            template: require('./zemGridCellInternalLink.component.html'),
            controller: function(
                $scope,
                zemNavigationNewService,
                zemUtils,
                $window
            ) {
                var vm = this;
                vm.openUrl = openUrl;

                $scope.$watch('ctrl.row', update);
                $scope.$watch('ctrl.data', update);

                function update() {
                    vm.href = null;
                    if (vm.data && vm.row.data && vm.row.entity) {
                        var includeQueryParams = true;
                        vm.href = zemNavigationNewService.getEntityHref(
                            vm.row.entity,
                            includeQueryParams
                        );
                    }
                }

                function openUrl($event) {
                    $event.preventDefault();
                    if (zemUtils.shouldOpenInNewTab($event)) {
                        $window.open(vm.href, '_blank');
                    } else {
                        NgZone.run(function() {
                            NgRouter.navigateByUrl(vm.href);
                        });
                    }
                }
            },
        };
    });
