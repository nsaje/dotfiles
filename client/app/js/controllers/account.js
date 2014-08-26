oneApp.controller('AccountCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.tabs = [
        {heading: 'Campaigns', route: 'main.accounts.campaigns', active: true, hidden: !$scope.hasPermission('zemauth.accounts_campaigns_view'), internal: $scope.isPermissionInternal('zemauth.accounts_campaign_view')}
    ];

    $scope.account = null;

    $scope.getAccount = function () {
        $scope.accounts.forEach(function (account) {
            if (account.id.toString() === $state.params.id) {
                $scope.account = account;
            }
        })
    };

    $scope.updateBreadcrumbAndTitle = function () {
        if (!$scope.account) {
            return;
        }
        $scope.setBreadcrumbAndTitle(
            [{name: $scope.account.name, state: 'main.accounts.campaigns({id: ' + $scope.account.id + '})', disabled: true }],
            $scope.account.name
        );
    };

    $scope.getAccount();
    $scope.updateBreadcrumbAndTitle();
}]);
