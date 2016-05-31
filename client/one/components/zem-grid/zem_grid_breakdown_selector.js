/* global oneApp */
'use strict';

oneApp.directive('zemGridBreakdownSelector', [function () {
    return {
        restrict: 'E',
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_breakdown_selector.html',
        link: function (scope, tElement) {
            // Prevent closing of dropdown-menu when checkbox is clicked.
            $(tElement).on('click', function (e) {
                e.stopPropagation();
            });
        },
        controller: ['zemGridStorageService', function (zemGridStorageService) {
            var vm = this;

            vm.levels = [
                {name: 'Level 1', breakdowns: ['b11', 'b12']},
                {name: 'Level 2', breakdowns: ['b21', 'b22']},
                {name: 'Level 3', breakdowns: ['b31']},
            ];

            init();

            function init () {
            }
        }],
    };
}]);
