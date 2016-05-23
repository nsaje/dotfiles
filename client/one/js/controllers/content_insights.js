/* globals oneApp */
oneApp.controller('ContentInsightsCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.infoboxLinkTo = 'main.campaigns.settings';
    $scope.summary = 'Titles';
    $scope.metric = 'CTR';
    $scope.rows = [];

    $scope.getTabs = function () {
        return [
            {
                heading: 'Ad groups',
                route: 'main.campaigns.ad_groups',
                active: true,
                hidden: $scope.campaign && $scope.campaign.archived,
                internal: false,
            },
            {
                heading: 'Media sources',
                route: 'main.campaigns.sources',
                active: false,
                hidden: $scope.campaign && $scope.campaign.archived,
                internal: false,
            },
            {
                heading: 'Agency',
                route: 'main.campaigns.agency',
                active: false,
                hidden: !$scope.hasPermission('zemauth.campaign_agency_view'),
                internal: $scope.isPermissionInternal('zemauth.campaign_agency_view'),
            },
            {
                heading: 'Settings',
                route: 'main.campaigns.archived',
                active: false,
                hidden: !$scope.campaign || !$scope.campaign.archived,
                internal: false,
            },
            {
                heading: 'Settings',
                route: 'main.campaigns.settings',
                active: false,
                hidden: $scope.campaign && $scope.campaign.archived,
                internal: false,
            },
            {
                heading: 'Budget',
                route: 'main.campaigns.budget',
                active: false,
                hidden: $scope.campaign && $scope.campaign.archived,
                internal: false,
            },
            ,
        ];
    };

    $scope.getSideTabs = function () {
        return [
            {
                heading: 'Ad groups',
                route: 'main.campaigns.ad_groups',
                active: true,
                hidden: $scope.campaign && $scope.campaign.archived,
                internal: false,
            },
            {
                heading: 'Content Insights',
                route: 'main.campaigns.content_insights',
                active: false,
                hidden: $scope.campaign && $scope.campaign.archived || !$scope.hasPermission('zemauth.campaign_content_insights_view'),
                internal: $scope.hasPermission('zemauth.campaign_content_insights_view'),
            }
        ];
    };

    $scope.setActiveTab = function () {
        $scope.tabs.forEach(function (tab) {
            tab.active = $state.is(tab.route);
        });

        $scope.sideTabs.forEach(function (sideTab) {
            sideTab.active = $state.is(sideTab.route);
        });
    };

    $scope.getInfoboxData = function () {
        api.campaignOverview.get(
            $state.params.id,
            $scope.dateRange.startDate,
            $scope.dateRange.endDate
        ).then(
            function (data) {
                $scope.infoboxHeader = data.header;
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
            }
        );
    };

    $scope.getContentInsights = function () {
        api.campaignContentInsights.get(
            $state.params.id,
            $scope.dateRange.startDate,
            $scope.dateRange.endDate
        ).then(
            function (data) {
                $scope.summary = data.summary;
                $scope.metric = data.metric;
                $scope.rows = data.rows;
            }
        );
    };

    $scope.init = function () {
        $scope.getInfoboxData();
        $scope.getContentInsights();
    };

    $scope.tabs = $scope.getTabs();
    $scope.sideTabs = $scope.getSideTabs();
    $scope.setActiveTab();
    $scope.init();
}]);
