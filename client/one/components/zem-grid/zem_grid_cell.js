/* globals angular */
'use strict';

angular.module('one.legacy').directive('zemGridCell', function () {

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
        templateUrl: '/components/zem-grid/templates/zem_grid_cell.html',
        controller: function (zemGridConstants) {
            var ctrl = this;
            ctrl.gridColumnTypes = zemGridConstants.gridColumnTypes;
            ctrl.type = getFieldType();

            function getFieldType () {
                if (!ctrl.col) {
                    return zemGridConstants.gridColumnTypes.BASE_FIELD;
                }

                var columnType = ctrl.col.type || zemGridConstants.gridColumnTypes.BASE_FIELD;

                if (zemGridConstants.gridColumnTypes.BASE_TYPES.indexOf(columnType) !== -1) {
                    if (ctrl.col.data && ctrl.col.data.editable) {
                        return zemGridConstants.gridColumnTypes.EDITABLE_BASE_FIELD;
                    }
                    return zemGridConstants.gridColumnTypes.BASE_FIELD;
                }

                if (zemGridConstants.gridColumnTypes.EXTERNAL_LINK_TYPES.indexOf(columnType) !== -1) {
                    return zemGridConstants.gridColumnTypes.EXTERNAL_LINK;
                }

                return columnType;
            }
        },
    };
});
