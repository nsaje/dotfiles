angular
    .module('one.widgets')
    .directive('zemGridCellPerformanceIndicator', function(zemGridConstants) {
        var statusIcons = {},
            statusClasses = {};
        statusIcons[constants.emoticon.HAPPY] = 'emoticon-happy-green.svg';
        statusClasses[constants.emoticon.HAPPY] = 'img-icon-happy';
        statusIcons[constants.emoticon.SAD] = 'emoticon-sad-red.svg';
        statusClasses[constants.emoticon.SAD] = 'img-icon-sad';
        statusIcons[constants.emoticon.NEUTRAL] = 'emoticon-neutral-gray.svg';
        statusClasses[constants.emoticon.NEUTRAL] = 'img-icon-neutral';

        function isFieldVisible(row) {
            return row.level !== zemGridConstants.gridRowLevel.FOOTER;
        }

        function getOverallIcon(overall) {
            if (overall) {
                return {
                    file: statusIcons[overall],
                    class: statusClasses[overall],
                };
            }
            return {
                file: statusIcons[constants.emoticon.NEUTRAL],
                class: statusClasses[constants.emoticon.NEUTRAL],
            };
        }

        function getStatusList(statuses) {
            if (!statuses) {
                return [];
            }

            var statusList = [];
            statuses.forEach(function(status) {
                statusList.push({
                    file: statusIcons[status.emoticon],
                    class: statusClasses[status.emoticon],
                    text: status.text,
                });
            });
            return statusList;
        }

        return {
            restrict: 'E',
            replace: true,
            scope: {},
            controllerAs: 'ctrl',
            bindToController: {
                data: '=',
                row: '=',
            },
            template: require('./zemGridCellPerformanceIndicator.component.html'),
            controller: function($scope, config) {
                var vm = this;

                vm.config = config;

                $scope.$watch('ctrl.row', update);
                $scope.$watch('ctrl.data', update);

                function update() {
                    vm.isFieldVisible = false;
                    vm.overall = getOverallIcon();
                    vm.statusList = [];

                    if (vm.row) {
                        vm.isFieldVisible = isFieldVisible(vm.row);
                    }

                    if (vm.data) {
                        vm.overall = getOverallIcon(vm.data.overall);
                        vm.statusList = getStatusList(vm.data.list);
                    }
                }
            },
        };
    });
