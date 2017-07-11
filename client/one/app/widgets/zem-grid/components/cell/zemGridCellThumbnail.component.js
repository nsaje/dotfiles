angular.module('one.widgets').directive('zemGridCellThumbnail', function () {

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
        templateUrl: '/app/widgets/zem-grid/components/cell/zemGridCellThumbnail.component.html',
        controller: function () {},
    };
});
