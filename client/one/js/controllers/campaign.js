/* globals oneApp,constants */
oneApp.controller('CampaignCtrl', ['$scope', '$state', '$location', 'zemNavigationService', 'campaignData', function ($scope, $state, $location, zemNavigationService, campaignData) { // eslint-disable-line max-len
    $scope.level = constants.level.CAMPAIGNS;
    $scope.isCampaignLanding = false;

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
            // this tab is only shown for archived campaigns
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
        ];
    };

    $scope.setActiveTab = function () {
        $scope.tabs.forEach(function (tab) {
            tab.active = $state.is(tab.route);
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

    $scope.isCampaignLanding = function () {
        return !!$scope.campaign.landingMode;
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

    $scope.setModels(campaignData);
    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();

    if ($scope.campaign && $scope.campaign.archived) {
        if ($scope.hasPermission('zemauth.campaign_agency_view')) {
            $state.go('main.campaigns.agency', {id: $scope.campaign.id});
        }

        $state.go('main.campaigns.settings', {id: $scope.campaign.id});
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

    $scope.hasInfoboxPermission = function () {
        return true;
    };
}]);
