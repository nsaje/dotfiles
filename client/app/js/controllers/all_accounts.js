/*globals oneApp*/

oneApp.controller('AllAccountsCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.tabs = [
        {heading: 'Accounts', route: 'main.all_accounts.accounts', active: true, hidden: !$scope.hasPermission('zemauth.all_accounts_accounts_view'), internal: $scope.isPermissionInternal('zemauth.all_accounts_accounts_view')}
    ];

    $scope.setBreadcrumbAndTitle([], 'All accounts');

    $scope.tabs.forEach(function(tab) {
        tab.active = $state.is(tab.route);
    });
}]);
