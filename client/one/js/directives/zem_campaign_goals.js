/* global oneApp,constants*/
'use strict';

oneApp.directive('zemCampaignGoals', ['$filter', function ($filter) {
    return {
        restrict: 'E',
        scope: {
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
            model: '=model',
            campaign: '=campaign',
            account: '=account',
            campaignGoals: '=goals',
        },
        templateUrl: '/partials/zem_campaign_goals.html',
        controller: ['$modal', '$scope', function ($modal, $scope) {
            $scope.campaignGoals = $scope.campaignGoals || [];
            $scope.i = 0;

            // Clear model
            $scope.model.added = [];
            $scope.model.modified = {};
            $scope.model.removed = [];
            $scope.model.primary = null;

            $scope.formatGoalValue = function (goal) {
                var value = $filter('number')(goal.value, 2);
                switch (goal.type) {
                case constants.campaignGoalKPI.TIME_ON_SITE:
                    return value + ' seconds';
                case constants.campaignGoalKPI.MAX_BOUNCE_RATE:
                    return value + '% bounce rate';
                case constants.campaignGoalKPI.PAGES_PER_SESSION:
                    return value + ' pages per session';
                case constants.campaignGoalKPI.CPA:
                    return '$' + value + ' CPA';
                case constants.campaignGoalKPI.CPC:
                    return '$' + value + ' CPC';
                case constants.campaignGoalKPI.CPM:
                    return '$' + value + ' CPM';
                case constants.campaignGoalKPI.NEW_UNIQUE_VISITORS:
                    return value + ' % new unique visitors';
                }
            };

            $scope.setPrimary = function (goal) {
                if (goal.removed) {
                    return;
                }
                $scope.campaignGoals.forEach(function (el) {
                    el.primary = false;
                });

                goal.primary = true;
                $scope.model.primary = goal.id || null;
            };

            $scope.deleteGoal = function (goal) {
                var index = $scope.campaignGoals.indexOf(goal);
                if (index === -1) {
                    return;
                }

                $scope.campaignGoals.splice(index, 1);

                if (goal.id === undefined) { // new goal
                    index = $scope.model.added.indexOf(goal);
                    if (index !== -1) {
                        $scope.model.added.splice(index, 1);
                    }
                } else {
                    goal.removed = true;
                    $scope.model.removed.push(goal);
                }

                if (goal.primary) {
                    goal.primary = false;
                    $scope.choosePrimary();
                }
            };

            $scope.choosePrimary = function () {
                if (!$scope.campaignGoals.length) {
                    return;
                }
                $scope.campaignGoals[0].primary = true;
                $scope.model.primary = $scope.campaignGoals[0].id;

                if (!$scope.model.primary) {
                    $scope.model.added[0].primary = true;
                }
            };

            function openModal (goal) {
                var scope = $scope.$new(true);

                scope.campaignGoals = $scope.campaignGoals;
                scope.campaign = $scope.campaign;
                scope.account = $scope.account;

                if (goal !== undefined) {
                    scope.campaignGoal = goal;
                }

                return $modal.open({
                    templateUrl: '/partials/edit_campaign_goal_modal.html',
                    controller: 'EditCampaignGoalModalCtrl',
                    windowClass: 'modal',
                    scope: scope,
                });
            }

            $scope.addGoal = function () {
                var modalInstance = openModal();

                modalInstance.result.then(function (campaignGoal) {
                    if (!$scope.campaignGoals.length) {
                        campaignGoal.primary = true;
                    }
                    $scope.campaignGoals.push(campaignGoal);
                    $scope.model.added.push(campaignGoal);
                });

                return modalInstance;
            };

            $scope.editGoal = function (goal) {
                var modalInstance = openModal(goal);
                modalInstance.result.then(function (campaignGoal) {
                    if (goal.id !== undefined) {
                        $scope.model.modified[goal.id] = campaignGoal.value;
                    }
                });

                return modalInstance;
            };
        }],
    };
}]);
