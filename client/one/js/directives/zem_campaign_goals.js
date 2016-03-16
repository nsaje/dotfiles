/* global oneApp,constants,angular*/
'use strict';

oneApp.directive('zemCampaignGoals', ['$filter', function ($filter) {

    return {
        restrict: 'E',
        scope: {
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
            model: '=model',
            campaign: '=campaign',
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
            };

            function openModal (goal) {
                var scope = $scope.$new(true);
                scope.campaign = $scope.campaign;
                if (goal !== undefined) {
                    scope.campaignGoal = goal;
                }
                scope.isGoalAvailable = function (option) {
                    var isAvailable = true,
                        countConversionGoals = 0;
                    if (goal && goal.type === option.value) {
                        return true;
                    }
                    $scope.campaignGoals.forEach(function (goal) {
                        if (goal.type === option.value) {
                            isAvailable = false;
                        }
                        countConversionGoals += goal.type === constants.campaignGoalKPI.CPA;
                    });
                    if (option.value === constants.campaignGoalKPI.CPA && countConversionGoals < 5) {
                        return true;
                    }
                    return isAvailable;
                };
                scope.validate = function (newGoal, allErrors) {
                    var goalTypeIds = {},
                        goalNames = {},
                        errors = {};
                    if (newGoal.type !== constants.campaignGoalKPI.CPA) {
                        return true;
                    }

                    goalNames[newGoal.conversionGoal.name] = 1;
                    goalTypeIds[
                        newGoal.conversionGoal.type + '::' + newGoal.conversionGoal.goalId
                    ] = 1;

                    $scope.campaignGoals.forEach(function (goal) {
                        if (goal.type !== constants.campaignGoalKPI.CPA) {
                            return;
                        }
                        var typeId = goal.conversionGoal.type + '::' + goal.conversionGoal.goalId;
                        if (!goalNames[goal.conversionGoal.name]) {
                            goalNames[goal.conversionGoal.name] = 0;
                        }
                        if (!goalTypeIds[typeId]) {
                            goalTypeIds[typeId] = 0;
                        }

                        goalNames[goal.conversionGoal.name]++;
                        goalTypeIds[typeId]++;
                    });
                    angular.forEach(goalTypeIds, function (count) {
                        if (count > 1) {
                            errors.goalId = ['This field has to be unique'];
                        }
                    });
                    angular.forEach(goalNames, function (count) {
                        if (count > 1) {
                            errors.name = ['This field has to be unique'];
                        }
                    });
                    if (errors.goalId || errors.name) {
                        allErrors.conversionGoal = errors;
                        return false;
                    }
                    return true;
                };

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
                    if (goal.id === undefined) {
                        $scope.model.modified[campaignGoal.id] = campaignGoal.value;
                    }
                });

                return modalInstance;
            };
        }],
    };
}]);
