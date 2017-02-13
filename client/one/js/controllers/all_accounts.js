/* globals angular, constants */

angular.module('one.legacy').controller('AllAccountsCtrl', function ($scope, $state) {
    $scope.level = constants.level.ALL_ACCOUNTS;
    $scope.tabs = [
      {heading: 'Accounts', route: 'main.allAccounts.accounts', active: true, hidden: !$scope.hasPermission('zemauth.all_accounts_accounts_view'), internal: $scope.isPermissionInternal('zemauth.all_accounts_accounts_view')},
      {heading: 'Media sources', route: 'main.allAccounts.sources', active: false, hidden: !$scope.hasPermission('zemauth.all_accounts_sources_view'), internal: $scope.isPermissionInternal('zemauth.all_accounts_sources_view')},
      {heading: 'Reports', route: 'main.allAccounts.scheduled_reports', active: false, hidden: $scope.hasPermission('zemauth.can_see_new_scheduled_reports'), internal: false},
    ];

    $scope.setActiveTab = function () {
        $scope.activeTab = 0;
        $scope.tabs.filter(function (tab) {
            return !tab.hidden;
        }).forEach(function (tab, index) {
            if ($state.is(tab.route)) {
                $scope.activeTab = index;
            }
        });
    };

    $scope.$on('$stateChangeSuccess', function () {
        $scope.setBreadcrumbAndTitle([], 'All accounts');
    });

    $scope.setActiveTab();
});
