/* globals angular, constants */
angular.module('one.legacy').controller('AdGroupCtrl', function ($scope, $state, $window, $location, api, zemNavigationService, adGroupData) { // eslint-disable-line max-len
    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.level = constants.level.AD_GROUPS;
    $scope.getTabs = function () {
        var tabs = [{
            heading: 'Content Ads',
            route: 'main.adGroups.ads',
            active: true,
            hidden: ($scope.adGroup && $scope.adGroup.archived === true),
        }, {
            heading: 'Media Sources',
            route: 'main.adGroups.sources',
            active: false,
            hidden: ($scope.adGroup && $scope.adGroup.archived === true),
        }, {
            heading: 'Publishers',
            route: 'main.adGroups.publishers',
            active: false,
            hidden: !$scope.hasPermission('zemauth.can_see_publishers') ||
                ($scope.adGroup && $scope.adGroup.archived === true),
            internal: $scope.isPermissionInternal('zemauth.can_see_publishers'),
        }, {
            heading: 'History',
            route: 'main.adGroups.history',
            active: false,
            hidden: !$scope.hasPermission('zemauth.ad_group_history_view') ||
                ($scope.adGroup && $scope.adGroup.archived === true) ||
                $scope.hasPermission('zemauth.can_see_history_in_drawer'),
            internal: $scope.isPermissionInternal('zemauth.ad_group_history_view'),
        }];

        return tabs;
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

    $scope.setInfoboxHeader = function (infoboxHeader) {
        $scope.infoboxHeader = infoboxHeader;
    };

    $scope.isAdGroupPaused = function () {
        return $scope.adGroup && $scope.adGroup.state === constants.settingsState.INACTIVE;
    };

    $scope.isInLanding = function () {
        return $scope.adGroup && $scope.adGroup.landingMode && !$scope.isAdGroupPaused();
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

    $scope.checkArchived = function () {
        if ($scope.adGroup && $scope.adGroup.archived) {
            $state.go('main.adGroups.archived', {id: $scope.adGroup.id});
        }
    };

    $scope.setModels(adGroupData);
    $scope.tabs = $scope.getTabs();
    $scope.setActiveTab();
    $scope.checkArchived();

    zemNavigationService.onUpdate($scope, function () {
        zemNavigationService.getAdGroup($state.params.id).then(function (adGroupData) {
            $scope.setModels(adGroupData);
            $scope.updateBreadcrumbAndTitle();
            $scope.updateInfoboxHeader();
            $scope.checkArchived();
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
});
