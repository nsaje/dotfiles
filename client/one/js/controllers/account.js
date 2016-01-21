/*globals oneApp*/

oneApp.controller('AccountCtrl', ['$scope', '$state', 'zemNavigationService', 'accountData', function ($scope, $state, zemNavigationService, accountData) {
    $scope.level = constants.level.ACCOUNTS;
    $scope.getTabs = function () {
        return [
            {heading: 'Campaigns', route: 'main.accounts.campaigns', active: true, hidden: !$scope.hasPermission('zemauth.account_campaigns_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived), internal: $scope.isPermissionInternal('zemauth.account_campaigns_view')},
            {heading: 'Media sources', route: 'main.accounts.sources', active: false, hidden: !$scope.hasPermission('zemauth.account_sources_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived), internal: $scope.isPermissionInternal('zemauth.account_sources_view')},
            {heading: 'Account', route: 'main.accounts.account', active: false, hidden: !$scope.hasPermission('zemauth.account_account_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived), internal: $scope.isPermissionInternal('zemauth.account_account_view')},
            {heading: 'Agency', route: 'main.accounts.agency', active: false, hidden: !$scope.hasPermission('zemauth.account_agency_view'), internal: $scope.isPermissionInternal('zemauth.account_agency_view')},
            {heading: 'Settings', route: 'main.accounts.settings', active: false, hidden: $scope.hasPermission('zemauth.account_agency_view') || !$scope.hasPermission('zemauth.view_archived_entities') || !$scope.account || !$scope.account.archived, internal: false},
            {heading: 'Credit', route: 'main.accounts.credit', active: false, hidden: !$scope.hasPermission('zemauth.account_credit_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived), internal: true},
            {heading: 'Reports', route: 'main.accounts.scheduled_reports', active: false, hidden: !$scope.hasPermission('zemauth.exports_plus') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived), internal: true},
        ];
    };
    $scope.setActiveTab = function () {
        $scope.tabs.forEach(function(tab) {
            tab.active = $state.is(tab.route);
        });
    };

    $scope.updateBreadcrumbAndTitle = function () {
        if (!$scope.account) {
            return;
        }
        $scope.setBreadcrumbAndTitle([{
                name: $scope.account.name,
                state: $scope.getDefaultAccountState(),
                params: {id: $scope.account.id},
                disabled: true
            }],
            $scope.account.name
        );
    };

    $scope.setModels(accountData);

    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();

    if ($scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived) {
        if ($scope.hasPermission('zemauth.account_agency_view')) {
            $state.go('main.accounts.agency', {id: $scope.account.id});
        } else {
            $state.go('main.accounts.settings', {id: $scope.account.id});
        }
    }

    $scope.$watch(zemNavigationService.lastSyncTS, function (newValue, oldValue) {
        zemNavigationService.getAccount($state.params.id).then(function(accountData) {
            $scope.setModels(accountData);
            $scope.updateBreadcrumbAndTitle();
        });
    });

    $scope.$watch('account.archived', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.tabs = $scope.getTabs();
            $scope.setActiveTab();
        }
    });

    $scope.$on('$stateChangeSuccess', function () {
        $scope.updateBreadcrumbAndTitle();
    });
}]);
