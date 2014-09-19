/*globals oneApp,moment,constants,options*/
oneApp.controller('MediaSourcesCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.type = null;

    var init = function () {
        if ($state.includes('main.allAccounts')) {
            $scope.type = 'all_accounts';
        } else if ($state.includes('main.accounts')) {
            $scope.type = 'account';
        } else if ($state.includes('main.campaigns')) {
            $scope.type = 'campaign';
        }
    };

    init();
}]);
