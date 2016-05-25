/* globals oneApp,constants */
'use strict';

oneApp.directive('zemSideTabset', function () {
    return {
        restrict: 'E',
        scope: {
            selected: '=',
            tabs: '=',
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
        },
        templateUrl: '/partials/zem_side_tabset.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
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
                        hidden: $scope.campaign && $scope.campaign.archived || !$scope.hasPermission('zemauth.campaign_content_insights_view'),
                        internal: $scope.hasPermission('zemauth.campaign_content_insights_view'),
                    }
                ];
            };

            $scope.tabClick = function (tab) {
                $scope.selected = tab;
            };

            $scope.tabs = $scope.getSideTabs();
            $scope.selected = { type: $scope.tabs[0].type };
        }]
    };
});
