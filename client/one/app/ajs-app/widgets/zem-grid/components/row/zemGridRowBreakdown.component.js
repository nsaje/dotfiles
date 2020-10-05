angular.module('one.widgets').directive('zemGridRowBreakdown', function() {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            row: '=',
            grid: '=',
        },
        template: require('./zemGridRowBreakdown.component.html'),
        controller: function(config, zemGridConstants, zemGridUIService) {
            // eslint-disable-line max-len
            var vm = this;
            vm.config = config;
            vm.loadMore = loadMore;
            vm.getBreakdownColumnStyle = getBreakdownColumnStyle;
            vm.getCompleteText = getCompleteText;

            function loadMore(limit) {
                var offset = vm.row.data.pagination.rowsLength;
                vm.grid.meta.api.loadData(vm.row, offset, limit);
            }

            function getBreakdownColumnStyle() {
                if (!vm.row) return;
                return zemGridUIService.getBreakdownColumnStyle(
                    vm.grid,
                    vm.row
                );
            }

            function getCompleteText() {
                if (!vm.row) return;
                if (vm.row.type !== zemGridConstants.gridRowType.BREAKDOWN)
                    return;

                var pagination = vm.row.data.pagination;
                if (vm.row.data.meta.error)
                    return "Error: Data can't be retrieved";
                if (pagination.count > 0) return 'All data loaded';
                if (pagination.count <= 0) return 'No data available';
            }
        },
    };
});
