/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridDebug', [function () {

    return {
        restrict: 'E',
        require: ['zemGridDebug'], replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_debug.html',
        controller: ['zemGridService', 'zemDataSourceService', 'zemDataSourceEndpoints', function (zemGridService, zemDataSourceService, zemDataSourceEndpoints) {
            this.DEBUG_BREAKDOWNS = {'ad_group': true, 'age': true, 'sex': false, 'date': true};

            this.applyBreakdown = function () {
                var breakdowns = [];
                angular.forEach(this.DEBUG_BREAKDOWNS, function (value, key) {
                    if (value) breakdowns.push(key);
                });

                var endpoint = zemDataSourceEndpoints.createMockEndpoint();
                endpoint.breakdowns = breakdowns;
                var dataSource = zemDataSourceService.createInstance(endpoint);
                zemGridService.loadGrid(dataSource).then(function (grid) {
                    this.grid = grid;
                    zemGridService.loadData(this.grid);
                }.bind(this));
            };

            this.toggleCollapseLevel = function (level) {
                zemGridService.toggleCollapseLevel(this.grid, level);
            };
        }],
    };
}]);
