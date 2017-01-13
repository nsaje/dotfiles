/* globals angular, constants */

angular.module('one.legacy').controller('AccountCtrl', function ($scope, $state, zemNavigationService, accountData) {
    $scope.level = constants.level.ACCOUNTS;
    $scope.getTabs = function () {
        return [
            {heading: 'Campaigns', route: 'main.accounts.campaigns', active: true, hidden: !$scope.hasPermission('zemauth.account_campaigns_view') || ($scope.account && $scope.account.archived === true), internal: $scope.isPermissionInternal('zemauth.account_campaigns_view')},
            {heading: 'Media sources', route: 'main.accounts.sources', active: false, hidden: !$scope.hasPermission('zemauth.account_sources_view') || ($scope.account && $scope.account.archived === true), internal: $scope.isPermissionInternal('zemauth.account_sources_view')},
            {heading: 'History', route: 'main.accounts.history', active: false, hidden: !$scope.hasPermission('zemauth.account_history_view') || ($scope.account && $scope.account.archived === true), internal: $scope.isPermissionInternal('zemauth.account_history_view')},
            {heading: 'Settings', route: 'main.accounts.archived', active: false, hidden: $scope.hasPermission('zemauth.account_account_view') || !$scope.account || !$scope.account.archived === true, internal: false},
            {heading: 'Pixels & Audiences', route: 'main.accounts.customAudiences', active: false, hidden: !$scope.hasPermission('zemauth.account_custom_audiences_view'), internal: $scope.isPermissionInternal('zemauth.account_custom_audiences_view')},
            {heading: 'Credit', route: 'main.accounts.credit', active: false, hidden: !$scope.hasPermission('zemauth.account_credit_view') || ($scope.account && $scope.account.archived === true), internal: true},
            {heading: 'Reports', route: 'main.accounts.scheduled_reports', active: false, hidden: ($scope.account && $scope.account.archived === true), internal: false},
        ];
    };
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

    $scope.checkArchived = function () {
        if ($scope.account && $scope.account.archived) {
            $state.go('main.accounts.archived', {id: $scope.account.id});
        }
    };

    $scope.setModels(accountData);

    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();
    $scope.checkArchived();

    zemNavigationService.onUpdate($scope, function () {
        zemNavigationService.getAccount($state.params.id).then(function (accountData) {
            $scope.setModels(accountData);
            $scope.updateBreadcrumbAndTitle();
            $scope.checkArchived();
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
});
