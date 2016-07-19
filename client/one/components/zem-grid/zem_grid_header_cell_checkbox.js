/* globals oneApp */
'use strict';

oneApp.directive('zemGridHeaderCellCheckbox', [function () {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_header_cell_checkbox.html',
        controller: ['$element', 'zemGridConstants', function ($element, zemGridConstants) {
            var vm = this;
            var pubsub = this.grid.meta.pubsub;

            vm.zemGridConstants = zemGridConstants;
            vm.options = vm.grid.meta.options.selection;
            vm.allFilterChecked = false;
            vm.getStyle = getStyle;
            vm.toggleAllFilter = toggleAllFilter;
            vm.selectCustomFilter = selectCustomFilter;

            initialize();

            function initialize () {
                initializeSelection();
                pubsub.register(pubsub.EVENTS.DATA_UPDATED, function () {
                    if (vm.grid.body.rows.length === 0) {
                        initializeSelection();
                    }
                });

                pubsub.register(pubsub.EVENTS.EXT_SELECTION_UPDATED, function () {
                    var selection = vm.grid.ext.selection;
                    var indeterminate =
                        selection.type === zemGridConstants.gridSelectionFilterType.CUSTOM ||
                        selection.selected.length > 0 || selection.unselected.length > 0;
                    $element.find('.allFilterCheckbox').prop ('indeterminate', indeterminate);
                });
            }

            function initializeSelection () {
                var defaultFilter = {
                    callback: function () {
                        return vm.allFilterChecked;
                    }
                };

                vm.grid.ext.selection = {
                    type: vm.allFilterChecked ?
                        zemGridConstants.gridSelectionFilterType.ALL :
                        zemGridConstants.gridSelectionFilterType.NONE,
                    filter: defaultFilter,
                    selected: [],
                    unselected: [],
                };
            }

            function toggleAllFilter ($event) {
                $event.stopPropagation();
                initializeSelection();
                pubsub.notify(pubsub.EVENTS.EXT_SELECTION_UPDATED, vm.grid.ext.selection);
            }

            function selectCustomFilter (filter) {
                vm.grid.ext.selection = {
                    type: zemGridConstants.gridSelectionFilterType.CUSTOM,
                    filter: filter,
                    selected: [],
                    unselected: [],
                };
                pubsub.notify(pubsub.EVENTS.EXT_SELECTION_UPDATED, vm.grid.ext.selection);
            }

            function getStyle () {
                var width = vm.options.filtersEnabled && vm.options.customFilters ? 60 : 40;
                return {
                    'max-width': width,
                    'min-width': width,
                };
            }
        }],
    };
}]);
