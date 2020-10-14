var TOTALS_LABEL_HELP_TEXT = require('../../../../../features/analytics/components/grid/grid-bridge/grid-bridge.component.constants')
    .TOTALS_LABEL_HELP_TEXT;

angular
    .module('one.widgets')
    .directive('zemGridCellBreakdownField', function() {
        var ENTITIES_WITH_INTERNAL_LINKS = [
            constants.entityType.ACCOUNT,
            constants.entityType.CAMPAIGN,
            constants.entityType.AD_GROUP,
        ];

        var ENTITIES_WITH_EXTERNAL_LINKS = [constants.entityType.CONTENT_AD];

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
            template: require('./zemGridCellBreakdownField.component.html'),
            controller: function(
                $scope,
                config,
                zemGridConstants,
                zemGridUIService
            ) {
                // eslint-disable-line max-len
                var vm = this;
                var collapseService = vm.grid.meta.collapseService;

                vm.config = config;
                vm.types = zemGridConstants.gridColumnTypes;
                vm.collapsable = false;
                vm.collapsed = false;
                vm.toggleCollapse = toggleCollapse;
                vm.getBreakdownColumnStyle = getBreakdownColumnStyle;
                vm.TOTALS_LABEL_HELP_TEXT = TOTALS_LABEL_HELP_TEXT;

                initialize();

                function initialize() {
                    var pubsub = vm.grid.meta.pubsub;
                    $scope.$watch('ctrl.row', updateModel);
                    $scope.$watch('ctrl.data', updateModel);
                    pubsub.register(
                        pubsub.EVENTS.EXT_COLLAPSE_UPDATED,
                        $scope,
                        updateModel
                    );

                    updateModel();
                }

                function updateModel() {
                    if (!vm.row) return;

                    vm.fieldType = getFieldType(
                        vm.grid.meta.data.breakdown,
                        vm.row
                    );
                    vm.collapsable = collapseService.isRowCollapsable(vm.row);
                    vm.collapsed = collapseService.isRowCollapsed(vm.row);
                }

                function getBreakdownColumnStyle() {
                    if (!vm.row) return; // can happen because of virtual scroll; TODO: find better solution
                    return zemGridUIService.getBreakdownColumnStyle(
                        vm.grid,
                        vm.row
                    );
                }

                function toggleCollapse() {
                    return collapseService.setRowCollapsed(
                        vm.row,
                        !vm.collapsed
                    );
                }

                function getFieldType(breakdown, row) {
                    // Footer row
                    if (row.level === zemGridConstants.gridRowLevel.FOOTER) {
                        return zemGridConstants.gridColumnTypes.TOTALS_LABEL;
                    }

                    if (
                        row.entity &&
                        ENTITIES_WITH_INTERNAL_LINKS.indexOf(
                            row.entity.type
                        ) !== -1
                    ) {
                        return zemGridConstants.gridColumnTypes.INTERNAL_LINK;
                    }

                    if (
                        row.entity &&
                        ENTITIES_WITH_EXTERNAL_LINKS.indexOf(
                            row.entity.type
                        ) !== -1
                    ) {
                        return zemGridConstants.gridColumnTypes.EXTERNAL_LINK;
                    }

                    return zemGridConstants.gridColumnTypes.BASE_FIELD;
                }
            },
        };
    });
