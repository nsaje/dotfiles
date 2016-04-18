/*globals oneApp*/

oneApp.controller('AllAccountsCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.level = constants.level.ALL_ACCOUNTS;
    $scope.tabs = [
        {heading: 'Accounts', route: 'main.allAccounts.accounts', active: true, hidden: !$scope.hasPermission('zemauth.all_accounts_accounts_view'), internal: $scope.isPermissionInternal('zemauth.all_accounts_accounts_view')},
        {heading: 'Media sources', route: 'main.allAccounts.sources', active: false, hidden: !$scope.hasPermission('zemauth.all_accounts_sources_view'), internal: $scope.isPermissionInternal('zemauth.all_accounts_sources_view')},
        {heading: 'Reports', route: 'main.allAccounts.scheduled_reports', active: false, hidden: !$scope.hasPermission('zemauth.exports_plus'), internal: $scope.isPermissionInternal('zemauth.exports_plus')},
    ];

    $scope.tabs.forEach(function (tab) {
        tab.active = $state.is(tab.route);
    });

    $scope.$on('$stateChangeSuccess', function () {
        $scope.setBreadcrumbAndTitle([], 'All accounts');
    });

    $scope.hasInfoboxPermission = function () {
        return $scope.hasPermission('zemauth.can_access_all_accounts_infobox');
    };

}]);
