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
            var selectionService = vm.grid.meta.selectionService;

            vm.allFilterChecked = false;
            vm.zemGridConstants = zemGridConstants;
            vm.isVisible = selectionService.isFilterSelectionEnabled;
            vm.getCustomFilters = selectionService.getCustomFilters;
            vm.toggleAllFilter = toggleAllFilter;
            vm.selectCustomFilter = selectCustomFilter;
            vm.getStyle = getStyle;

            initialize();

            function initialize () {
                pubsub.register(pubsub.EVENTS.EXT_SELECTION_UPDATED, function () {
                    var selection = selectionService.getSelection();
                    var indeterminate =
                        selection.type === zemGridConstants.gridSelectionFilterType.CUSTOM ||
                        selection.selected.length > 0 || selection.unselected.length > 0;
                    $element.find('.allFilterCheckbox').prop ('indeterminate', indeterminate);
                });
            }

            function toggleAllFilter ($event) {
                $event.stopPropagation();
                var type = vm.allFilterChecked ?
                    zemGridConstants.gridSelectionFilterType.ALL :
                    zemGridConstants.gridSelectionFilterType.NONE;
                selectionService.setFilter(type);
            }

            function selectCustomFilter (filter) {
                selectionService.setFilter(zemGridConstants.gridSelectionFilterType.CUSTOM, filter);
            }

            function getStyle () {
                var width = vm.isVisible() && vm.getCustomFilters() ? 60 : 40;
                return {
                    'max-width': width,
                    'min-width': width,
                };
            }
        }],
    };
}]);
