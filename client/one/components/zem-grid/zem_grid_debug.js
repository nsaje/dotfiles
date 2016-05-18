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
            pubsub: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_debug.html',
        controller: ['zemGridService', function (zemGridService) {

            this.source = this.grid.meta.source;
            this.availableBreakdowns = {};
            this.source.availableBreakdowns.forEach(function (breakdown) {
                this.availableBreakdowns[breakdown] = this.source.selectedBreakdown.indexOf(breakdown) > -1;
            }.bind(this));

            this.applyBreakdown = function () {
                var selectedBreakdown = [];
                angular.forEach(this.availableBreakdowns, function (value, key) {
                    if (value) selectedBreakdown.push(key);
                });
                this.grid.meta.source.selectedBreakdown = selectedBreakdown;
                zemGridService.loadData(this.grid).then(function () {
                    this.pubsub.notify(this.pubsub.EVENTS.ROWS_UPDATED);
                }).bind(this);
            };

            this.toggleCollapseLevel = function (level) {
                zemGridService.toggleCollapseLevel(this.grid, level);
                $scope.ctrl.pubsub.notify($scope.ctrl.pubsub.EVENTS.ROWS_UPDATED);
            };
        }],
    };
}]);
