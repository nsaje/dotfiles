angular.module('one.widgets').directive('zemGridCellThumbnail', function() {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            column: '=',
            row: '=',
            grid: '=',
        },
        template: require('./zemGridCellThumbnail.component.html'),
        controller: function() {},
    };
});
