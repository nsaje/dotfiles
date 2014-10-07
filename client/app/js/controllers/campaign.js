/*globals oneApp,$,moment*/
oneApp.controller('CampaignCtrl', ['$scope', '$state', '$location', function ($scope, $state, $location) {
    $scope.level = constants.level.CAMPAIGNS;
    $scope.getTabs = function () {
        return [
            {heading: 'Ad groups', route: 'main.campaigns.ad_groups', active: true, hidden: !$scope.hasPermission('zemauth.campaign_ad_groups_view') || ($scope.campaign && $scope.campaign.archived), internal: $scope.isPermissionInternal('zemauth.campaign_ad_groups_view')},
            {heading: 'Media sources', route: 'main.campaigns.sources', active: false, hidden: !$scope.hasPermission('zemauth.campaign_sources_view') || ($scope.campaign && $scope.campaign.archived), internal: $scope.isPermissionInternal('zemauth.campaign_sources_view')},
            {heading: 'Agency', route: 'main.campaigns.agency', active: false, hidden: !$scope.hasPermission('zemauth.campaign_settings_view'), internal: $scope.isPermissionInternal('zemauth.campaign_settings_view')},
            {heading: 'Budget', route: 'main.campaigns.budget', active: false, hidden: !$scope.hasPermission('zemauth.campaign_budget_management_view') || ($scope.campaign && $scope.campaign.archived), internal: $scope.isPermissionInternal('zemauth.campaign_budget_management_view')}
        ];
    };
    $scope.setActiveTab = function () {
        $scope.tabs.forEach(function(tab) {
            tab.active = $state.is(tab.route);
        });
    };

    $scope.setAccount(null);
    $scope.setCampaign(null);

    $scope.getModels = function () {
        $scope.accounts.forEach(function (account) {
            account.campaigns.forEach(function (campaign) {
                if (campaign.id.toString() === $state.params.id) {
                    $scope.setAccount(account);
                    $scope.setCampaign(campaign);
                }
            });
        });
    };

    $scope.updateBreadcrumbAndTitle = function () {
        if (!$scope.accounts) {
            return;
        }
        $scope.setBreadcrumbAndTitle(
            [{name: $scope.account.name, state: $scope.getDefaultAccountState() + '({id: ' + $scope.account.id + '})', disabled: !$scope.canAccessAccounts()},
            {name: $scope.campaign.name, state: $scope.getDefaultCampaignState() + '({id: ' + $scope.campaign.id + '})', disabled: true}],
            $scope.campaign.name
        );
    };

    $scope.updateAccounts = function (newCampaignName) {
        if (!$scope.accounts || !newCampaignName) {
            return;
        }
        $scope.campaign.name = newCampaignName;
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('page', null);
        $location.search('size', null);
        $location.search('order', null);
    });

    $scope.getModels();
    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();

    if ($scope.campaign && $scope.campaign.archived && !$state.is('main.campaigns.agency')) {
        $state.go('main.campaigns.agency', {id: $scope.campaign.id});
    } else if ($scope.account && $scope.account.archived && !$state.is('main.accounts.agency')) {
        $state.go('main.accounts.agency', {id: $scope.account.id});
    }

    $scope.updateBreadcrumbAndTitle();

    $scope.$watch('campaign.archived', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.tabs = $scope.getTabs();
            $scope.setActiveTab();
        }
    });
}]);
