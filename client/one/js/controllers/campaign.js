/* globals angular, constants */
angular.module('one.legacy').controller('CampaignCtrl', ['$scope', '$state', '$location', 'zemNavigationService', 'campaignData', 'api', 'zemDataFilterService', function ($scope, $state, $location, zemNavigationService, campaignData, api, zemDataFilterService) { // eslint-disable-line max-len
    $scope.level = constants.level.CAMPAIGNS;
    $scope.contentInsights = {
        summary: null,
        metric: null,
        bestPerformerRows: [],
        worstPerformerRows: [],
    };
    $scope.selectedSideTab = {tab: {type: constants.sideBarTabs.PERFORMANCE}};
    $scope.isChartVisible = true;
    $scope.isContentInsightsVisible = false;
    $scope.$watch('selectedSideTab.tab', function (newValue) {
        if (newValue.type === constants.sideBarTabs.PERFORMANCE) {
            $scope.isChartVisible = true;
            $scope.isContentInsightsVisible = false;
            $scope.reflowGraph(0);
        } else if (newValue.type === constants.sideBarTabs.CONTENT_INSIGHTS) {
            $scope.isChartVisible = false;
            $scope.isContentInsightsVisible = true;
            $scope.reflowGraph(0);
        }
    });
    $scope.getTabs = function () {
        return [
            {
                heading: 'Ad groups',
                route: 'main.campaigns.ad_groups',
                active: true,
                hidden: $scope.campaign && $scope.campaign.archived === true,
                internal: false,
            },
            {
                heading: 'Media sources',
                route: 'main.campaigns.sources',
                active: false,
                hidden: $scope.campaign && $scope.campaign.archived === true,
                internal: false,
            },
            {
                heading: 'Settings',
                route: 'main.campaigns.settings',
                active: false,
                hidden: $scope.campaign && $scope.campaign.archived === true,
                internal: false,
            },
            {
                heading: 'History',
                route: 'main.campaigns.history',
                active: false,
                hidden: $scope.campaign && $scope.campaign.archived === true ||
                    !$scope.hasPermission('zemauth.campaign_history_view'),
                internal: $scope.isPermissionInternal('zemauth.campaign_history_view'),
            },
            {
                heading: 'Budget',
                route: 'main.campaigns.budget',
                active: false,
                hidden: $scope.campaign && $scope.campaign.archived === true,
                internal: false,
            },
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
        if (!$scope.account || !$scope.campaign) {
            return;
        }
        $scope.setBreadcrumbAndTitle([{
            name: $scope.account.name,
            state: $scope.getDefaultAccountState(),
            params: {id: $scope.account.id},
            disabled: !$scope.canAccessAccounts(),
        }, {
            name: $scope.campaign.name,
            state: $scope.getDefaultCampaignState(),
            params: {id: $scope.campaign.id},
            disabled: true,
        }],
            $scope.campaign.name
        );
    };

    $scope.isInLanding = function () {
        return $scope.campaign && !!$scope.campaign.landingMode;
    };

    $scope.manageBudget = function () {
        $state.go('main.campaigns.budget', {id: $scope.campaign.id});
    };

    $scope.$on('$stateChangeStart', function () {
        $location.search('page', null);
    });

    $scope.$on('$stateChangeSuccess', function () {
        $scope.updateBreadcrumbAndTitle();
    });

    $scope.getContentInsights = function () {
        if (!$scope.hasPermission('zemauth.can_view_sidetabs')) {
            return;
        }
        if (!$scope.hasPermission('zemauth.can_view_campaign_content_insights_side_tab')) {
            return;
        }
        var dateRange = zemDataFilterService.getDateRange();
        api.campaignContentInsights.get(
            $state.params.id,
            dateRange.startDate,
            dateRange.endDate
        ).then(
            function (data) {
                $scope.contentInsights = data;
            }
        );
    };

    $scope.setModels(campaignData);
    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();

    if ($scope.campaign && $scope.campaign.archived) {
        $state.go('main.campaigns.archived', {id: $scope.campaign.id});
    }

    zemNavigationService.onUpdate($scope, function () {
        zemNavigationService.getCampaign($state.params.id).then(function (campaignData) {
            $scope.setModels(campaignData);
            $scope.updateBreadcrumbAndTitle();
        });
    });

    $scope.$watch('campaign.archived', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.tabs = $scope.getTabs();
            $scope.setActiveTab();
        }
    });
}]);
