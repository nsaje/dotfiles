/*globals oneApp*/

oneApp.controller('AccountCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.tabs = [
        {heading: 'Campaigns', route: 'main.accounts.campaigns', active: true, hidden: !$scope.hasPermission('zemauth.account_campaigns_view'), internal: $scope.isPermissionInternal('zemauth.account_campaigns_view')},
        {heading: 'Agency', route: 'main.accounts.agency', active: false, hidden: !$scope.hasPermission('zemauth.account_agency_view'), internal: $scope.isPermissionInternal('zemauth.account_agency_view')}
    ];
    $scope.account = null;

    $scope.getAccount = function () {
        $scope.accounts.forEach(function (account) {
            if (account.id.toString() === $state.params.id) {
                $scope.account = account;
            }
        });
    };

    $scope.updateBreadcrumbAndTitle = function () {
        if (!$scope.account) {
            return;
        }
        $scope.setBreadcrumbAndTitle(
            [{name: $scope.account.name, state: $scope.getDefaultAccountState() + '({id: ' + $scope.account.id + '})', disabled: true }],
            $scope.account.name
        );
    };

    $scope.updateAccounts = function (newAccountName) {
        if (!newAccountName) {
            return;
        }
        $scope.account.name = newAccountName;
    };

    $scope.getAccount();
    $scope.updateBreadcrumbAndTitle();

    $scope.tabs.forEach(function(tab) {
        tab.active = $state.is(tab.route);
    });
}]);
