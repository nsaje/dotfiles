angular.module('one.widgets').directive('zemGridCell', function() {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            col: '=',
            data: '=',
            row: '=',
            grid: '=',
        },
        template: require('./zemGridCell.component.html'),
        controller: function($scope, zemGridConstants) {
            var ctrl = this;
            ctrl.gridColumnTypes = zemGridConstants.gridColumnTypes;
            ctrl.type = getFieldType();
            ctrl.gridBodyElement = getGridBodyElement();
            ctrl.canSeePublisherBidModifierCell = canSeePublisherBidModifierCell;
            ctrl.canSeeBidModifierCell = canSeeBidModifierCell;
            ctrl.updateBidModifier = updateBidModifier;

            $scope.$watch('ctrl.col', function() {
                ctrl.type = getFieldType();
            });

            function getFieldType() {
                if (!ctrl.col) {
                    return zemGridConstants.gridColumnTypes.BASE_FIELD;
                }

                var columnType =
                    ctrl.col.type ||
                    zemGridConstants.gridColumnTypes.BASE_FIELD;

                if (
                    zemGridConstants.gridColumnTypes.BASE_TYPES.indexOf(
                        columnType
                    ) !== -1
                ) {
                    if (ctrl.col.data && ctrl.col.data.editable) {
                        return zemGridConstants.gridColumnTypes
                            .EDITABLE_BASE_FIELD;
                    }
                    return zemGridConstants.gridColumnTypes.BASE_FIELD;
                }

                if (
                    zemGridConstants.gridColumnTypes.EXTERNAL_LINK_TYPES.indexOf(
                        columnType
                    ) !== -1
                ) {
                    return zemGridConstants.gridColumnTypes.EXTERNAL_LINK;
                }

                return columnType;
            }

            function getGridBodyElement() {
                if (ctrl.grid) {
                    return ctrl.grid.body.ui.element[0];
                }
            }

            function canSeePublisherBidModifierCell() {
                if (
                    !ctrl.row ||
                    ctrl.row.level === zemGridConstants.gridRowLevel.FOOTER
                ) {
                    return false;
                }

                if (!ctrl.data || !ctrl.data.value) {
                    return false;
                }

                return (
                    getFieldType() ===
                        zemGridConstants.gridColumnTypes.BID_MODIFIER_FIELD &&
                    ctrl.grid.meta.data.breakdown ===
                        constants.breakdown.PUBLISHER
                );
            }

            function canSeeBidModifierCell() {
                if (
                    !ctrl.row ||
                    ctrl.row.level === zemGridConstants.gridRowLevel.FOOTER
                ) {
                    return false;
                }

                if (!ctrl.data || !ctrl.data.value) {
                    return false;
                }

                return (
                    getFieldType() ===
                        zemGridConstants.gridColumnTypes.BID_MODIFIER_FIELD &&
                    ctrl.grid.meta.data.breakdown !==
                        constants.breakdown.PUBLISHER
                );
            }

            function updateBidModifier($event) {
                ctrl.data.value = $event;
            }
        },
    };
});
