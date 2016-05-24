/*globals oneApp*/
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
                        heading: 'Ad groups',
                        hidden: $scope.campaign && $scope.campaign.archived,
                        internal: false,
                        cls: 'performance',
                    },
                    {
                        heading: 'Content Insights',
                        hidden: $scope.campaign && $scope.campaign.archived || !$scope.hasPermission('zemauth.campaign_content_insights_view'),
                        internal: $scope.hasPermission('zemauth.campaign_content_insights_view'),
                        cls: 'content-insights',
                    }
                ];
            };

            $scope.tabClick = function (tab) {
                $scope.selected = tab;
            };

            $scope.tabs = $scope.getSideTabs();
            $scope.selected = { tab: $scope.tabs[0] };
        }]
    };
});
