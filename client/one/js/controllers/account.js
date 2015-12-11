/*globals oneApp*/

oneApp.controller('AccountCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.level = constants.level.ACCOUNTS;
    $scope.getTabs = function () {
        return [
            {heading: 'Campaigns', route: 'main.accounts.campaigns', active: true, hidden: !$scope.hasPermission('zemauth.account_campaigns_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived), internal: $scope.isPermissionInternal('zemauth.account_campaigns_view')},
            {heading: 'Media sources', route: 'main.accounts.sources', active: false, hidden: !$scope.hasPermission('zemauth.account_sources_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived), internal: $scope.isPermissionInternal('zemauth.account_sources_view')},
            {heading: 'Account', route: 'main.accounts.account', active: false, hidden: !$scope.hasPermission('zemauth.account_account_view'), internal: $scope.isPermissionInternal('zemauth.account_account_view')},
            {heading: 'Agency', route: 'main.accounts.agency', active: false, hidden: !$scope.hasPermission('zemauth.account_agency_view'), internal: $scope.isPermissionInternal('zemauth.account_agency_view')},
            {heading: 'Settings', route: 'main.accounts.settings', active: false, hidden: $scope.hasPermission('zemauth.account_agency_view') || !$scope.hasPermission('zemauth.view_archived_entities') || !$scope.account || !$scope.account.archived, internal: false},
            {heading: 'Credit', route: 'main.accounts.credit', active: false, hidden: !$scope.hasPermission('zemauth.account_credit_view') || (!$scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived), internal: true},
            {heading: 'Reports', route: 'main.accounts.scheduled_reports', active: false, hidden: !$scope.hasPermission('zemauth.exports_plus') || (!$scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived), internal: true},
        ];
    };
    $scope.setActiveTab = function () {
        $scope.tabs.forEach(function(tab) {
            tab.active = $state.is(tab.route);
        });
    };

    $scope.setAccount(null);

    $scope.getAccount = function () {
        $scope.accounts.forEach(function (account) {
            if (account.id.toString() === $state.params.id.toString()) {
                $scope.setAccount(account);
            }
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

    $scope.updateAccounts = function (newAccountName) {
        if (!newAccountName) {
            return;
        }
        $scope.account.name = newAccountName;
    };

    $scope.getAccount();

    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();

    if ($scope.hasPermission('zemauth.view_archived_entities') && $scope.account && $scope.account.archived) {
        if ($scope.hasPermission('zemauth.account_agency_view')) {
            $state.go('main.accounts.agency', {id: $scope.account.id});
        } else {
            $state.go('main.accounts.settings', {id: $scope.account.id});
        }
    }

    $scope.$watch('accounts', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.getAccount();
        }
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
