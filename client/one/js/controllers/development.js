/* globals oneApp */

oneApp.controller('DevelopmentCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.$on('$stateChangeSuccess', function () {
        // if ($state.is('main.development.grid') &&
        //     $scope.hasPermission('zemauth.can_access_table_breakdowns_development_features')) {
        //     return;
        // }
        //
        // $state.go('main');
    });
}]);
