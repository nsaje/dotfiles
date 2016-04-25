/* globals oneApp,constants */
oneApp.controller('AdGroupCtrl', ['$scope', '$state', '$window', '$location', 'api', 'zemNavigationService', 'adGroupData', function ($scope, $state, $window, $location, api, zemNavigationService, adGroupData) { // eslint-disable-line max-len
    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.level = constants.level.AD_GROUPS;
    $scope.getTabs = function () {
        var tabs = [{
            heading: 'Content Ads',
            route: 'main.adGroups.ads',
            active: true,
            hidden: ($scope.adGroup && $scope.adGroup.archived),
        }, {
            heading: 'Media Sources',
            route: 'main.adGroups.sources',
            active: false,
            hidden: ($scope.adGroup && $scope.adGroup.archived),
        }, {
            heading: 'Publishers',
            route: 'main.adGroups.publishers',
            active: false,
            hidden: !$scope.hasPermission('zemauth.can_see_publishers') ||
                ($scope.adGroup && $scope.adGroup.archived),
            internal: $scope.isPermissionInternal('zemauth.can_see_publishers'),
        }, {
            heading: 'Settings',
            route: 'main.adGroups.settings',
            active: false,
            hidden: (!$scope.hasPermission('dash.settings_view')) ||
                (!$scope.hasPermission('dash.settings_view') && !($scope.adGroup && $scope.adGroup.archived)) ||
                ($scope.hasPermission('zemauth.ad_group_agency_tab_view') &&
                 ($scope.adGroup && $scope.adGroup.archived)),
        }, {
            heading: 'Agency',
            route: 'main.adGroups.agency',
            active: false,
            hidden: !$scope.hasPermission('zemauth.ad_group_agency_tab_view'),
            internal: $scope.isPermissionInternal('zemauth.ad_group_agency_tab_view'),
        }];

        return tabs;
    };

    $scope.setActiveTab = function () {
        if ($scope.tabs === undefined && $window.isDemo) {
            // when someone refreshes the page on a demo campaign/adgroup
            // client breaks before demo can figure it out.
            // this resets the demo to its defaults
            $window.onbeforeunload = null;
            $window.location.href = '';
        }
        $scope.tabs.forEach(function (tab) {
            tab.active = $state.is(tab.route);
        });
    };

    $scope.setInfoboxHeader = function (infoboxHeader) {
        $scope.infoboxHeader = infoboxHeader;
    };

    $scope.isAdGroupPaused = function () {
        return $scope.adGroup && $scope.adGroup.state === constants.adGroupSettingsState.INACTIVE;
    };

    $scope.isCampaignLanding = function () {
        return $scope.adGroup && $scope.adGroup.state === constants.adGroupSettingsState.ACTIVE &&
            $scope.campaign && $scope.campaign.landingMode;
    };

    $scope.manageBudget = function () {
        $state.go('main.campaigns.budget', {id: $scope.campaign.id});
    };

    $scope.setAdGroupData = function (key, value) {
        var data = $scope.adGroupData[$state.params.id] || {};
        data[key] = value;
        $scope.adGroupData[$state.params.id] = data;
    };

    $scope.updateBreadcrumbAndTitle = function () {
        if (!$scope.account || !$scope.campaign || !$scope.adGroup) {
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
            disabled: !$scope.canAccessCampaigns(),
        }, {
            name: $scope.adGroup.name,
            state: $scope.getDefaultAdGroupState(),
            params: {id: $scope.adGroup.id},
            disabled: true,
        }],
            $scope.adGroup.name + ' - ' + $scope.campaign.name
        );
    };

    $scope.updateInfoboxHeader = function () {
        zemNavigationService.getAdGroup($state.params.id).then(function (adGroupData) {
            if ($scope.infoboxHeader) {
                $scope.infoboxHeader.active = adGroupData.adGroup.reloading ? 'reloading' : adGroupData.adGroup.active;
            }
        });
    };

    $scope.$on('$stateChangeStart', function () {
        $location.search('source_ids', null);
        $location.search('source_totals', null);
        $location.search('page', null);
    });

    $scope.$on('$stateChangeSuccess', function () {
        $scope.updateBreadcrumbAndTitle();
        $scope.setActiveTab();
    });

    $scope.setModels(adGroupData);
    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();

    if ($scope.adGroup && $scope.adGroup.archived) {
        if ($scope.hasPermission('zemauth.ad_group_agency_tab_view')) {
            $state.go('main.adGroups.agency', {id: $scope.adGroup.id});
        } else {
            $state.go('main.adGroups.settings', {id: $scope.adGroup.id});
        }
    }

    zemNavigationService.onUpdate($scope, function () {
        zemNavigationService.getAdGroup($state.params.id).then(function (adGroupData) {
            $scope.setModels(adGroupData);
            $scope.updateBreadcrumbAndTitle();
            $scope.updateInfoboxHeader();
        });
    });

    zemNavigationService.onAdGroupLoading($scope, $state.params.id, function () {
        $scope.updateInfoboxHeader();
    });

    $scope.$watch('adGroup.archived', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.tabs = $scope.getTabs();
            $scope.setActiveTab();
        }
    });
}]);
