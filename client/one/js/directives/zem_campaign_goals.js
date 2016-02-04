/* global angular,oneApp,constants,options*/
'use strict';

oneApp.directive('zemCampaignGoals', [function () {

    return {
        restrict: 'E',
        scope: {
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
        },
        templateUrl: '/partials/zem_campaign_goals.html',
        controller: ['$modal', '$scope', function ($modal, $scope) {
            $scope.campaignGoals = [];

            $scope.formatGoalValue = function (goal) {
                switch (goal.type) {
                case constants.campaignGoalKPI.TIME_ON_SITE:
                    return goal.value + ' seconds';
                case constants.campaignGoalKPI.MAX_BOUNCE_RATE:
                    return goal.value + '% bounce rate';
                case constants.campaignGoalKPI.PAGES_PER_SESSION:
                    return goal.value + ' pages per session';
                case constants.campaignGoalKPI.CPA:
                    return '$' + goal.value + ' CPA';
                case constants.campaignGoalKPI.CPC:
                    return '$' + goal.value + ' CPC';
                case constants.campaignGoalKPI.CPM:
                    return '$' + goal.value + ' CPM';
                }
            };

            $scope.setPrimary = function (goal) {
                $scope.campaignGoals.forEach(function (el) {
                    el.primary = false;
                });

                goal.primary = true;
            };

            $scope.removeGoal = function (goal) {
                var index = $scope.campaignGoals.indexOf(goal);
                if (index > -1) {
                    $scope.campaignGoals.splice(index, 1);
                }
            };

            $scope.editGoal = function (goal) {
                var scope = $scope.$new(true);

                if (goal !== undefined) {
                    scope.campaignGoal = goal;
                }

                var modalInstance = $modal.open({
                    templateUrl: '/partials/edit_campaign_goal_modal.html',
                    controller: 'EditCampaignGoalModalCtrl',
                    windowClass: 'modal',
                    scope: scope,
                });

                return modalInstance;
            };

            $scope.saveGoalValue = function (rowId, val, callback) {
                $scope.campaignGoals.filter(function (el) {
                    return el.id === rowId;
                }).forEach(function (el) {
                    el.value = val;
                });

                callback();
            };
        }],
    };
}]);
