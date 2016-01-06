/*globals oneApp,$,moment*/
oneApp.controller('CampaignCtrl', ['$scope', '$state', '$location', function ($scope, $state, $location) {
    $scope.level = constants.level.CAMPAIGNS;
    $scope.getTabs = function ()
    {
        return [
            {heading: 'Ad groups', route: 'main.campaigns.ad_groups', active: true, hidden: !$scope.hasPermission('zemauth.campaign_ad_groups_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.campaign && $scope.campaign.archived), internal: $scope.isPermissionInternal('zemauth.campaign_ad_groups_view')},
            {heading: 'Media sources', route: 'main.campaigns.sources', active: false, hidden: !$scope.hasPermission('zemauth.campaign_sources_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.campaign && $scope.campaign.archived), internal: $scope.isPermissionInternal('zemauth.campaign_sources_view')},
            {heading: 'Agency', route: 'main.campaigns.agency', active: false, hidden: !$scope.hasPermission('zemauth.campaign_agency_view'), internal: $scope.isPermissionInternal('zemauth.campaign_agency_view')},
            {heading: 'Budget', route: 'main.campaigns.budget', active: false, hidden: !$scope.hasPermission('zemauth.campaign_budget_management_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.campaign && $scope.campaign.archived), internal: $scope.isPermissionInternal('zemauth.campaign_budget_management_view')},
            // this tab is only shown for archived campaigns
            {heading: 'Settings', route: 'main.campaigns.archived', active: false, hidden: $scope.hasPermission('zemauth.campaign_settings_view') || !$scope.hasPermission('zemauth.view_archived_entities') || !$scope.campaign || !$scope.campaign.archived, internal: false},
            {heading: 'Settings', route: 'main.campaigns.settings', active: false, hidden: !$scope.hasPermission('zemauth.campaign_settings_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.campaign && $scope.campaign.archived), internal: $scope.isPermissionInternal('zemauth.campaign_settings_view')},
            {heading: 'Budget +', route: 'main.campaigns.budget_plus', active: false, hidden: !$scope.hasPermission('zemauth.campaign_budget_view') || ($scope.hasPermission('zemauth.view_archived_entities') && $scope.campaign && $scope.campaign.archived), internal: $scope.isPermissionInternal('zemauth.campaign_budget_view')}
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
                if (campaign.id.toString() === $state.params.id.toString()) {
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
        $scope.setBreadcrumbAndTitle([{
                name: $scope.account.name,
                state: $scope.getDefaultAccountState(),
                params: {id: $scope.account.id},
                disabled: !$scope.canAccessAccounts()
            }, {
                name: $scope.campaign.name,
                state: $scope.getDefaultCampaignState(),
                params: {id: $scope.campaign.id},
                disabled: true
            }],
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
    });

    $scope.$on('$stateChangeSuccess', function () {
        $scope.updateBreadcrumbAndTitle();
    });

    $scope.getModels();
    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();

    if ($scope.hasPermission('zemauth.view_archived_entities') && $scope.campaign && $scope.campaign.archived) {
        if ($scope.hasPermission('zemauth.campaign_agency_view')) {
            $state.go('main.campaigns.agency', {id: $scope.campaign.id});
        } else if ($scope.hasPermission('zemauth.campaign_settings_view')) {
            $state.go('main.campaigns.settings', {id: $scope.campaign.id});
        } else {
            $state.go('main.campaigns.archived', {id: $scope.campaign.id});
        }
    }

    $scope.$watch('accounts', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.getModels();
        }
    });

    $scope.$watch('campaign.archived', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.tabs = $scope.getTabs();
            $scope.setActiveTab();
        }
    });
}]);
