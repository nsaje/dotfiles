/* globals oneApp,constants */
'use strict';

oneApp.directive('zemSideTabset', function () {
    return {
        restrict: 'E',
        scope: {
            selected: '=zemSelected',
            tabs: '=',
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
        },
        templateUrl: '/partials/zem_side_tabset.html',
        controller: ['$scope', function ($scope) {
            $scope.getSideTabs = function () {
                return [
                    {
                        type: constants.sideBarTabs.PERFORMANCE,
                        heading: 'Ad groups',
                        hidden: $scope.campaign && $scope.campaign.archived,
                        internal: false,
                    },
                    {
                        type: constants.sideBarTabs.CONTENT_INSIGHTS,
                        heading: 'Content Insights',
                        hidden: !$scope.hasPermission('zemauth.can_view_campaign_content_insights_side_tab'),
                        internal: $scope.isPermissionInternal('zemauth.can_view_campaign_content_insights_side_tab'),
                    },
                ];
            };

            $scope.countVisibleTabs = function (tabs) {
                var count = 0;
                tabs.forEach(function (tab) {
                    if (!tab.hidden) count++;
                });
                return count;
            };

            $scope.tabClick = function (tab) {
                $scope.selected = tab;
            };

            $scope.tabs = $scope.getSideTabs();
            $scope.visibleTabCount = $scope.countVisibleTabs($scope.tabs);
            $scope.selected = $scope.tabs[0];
        }],
    };
});
