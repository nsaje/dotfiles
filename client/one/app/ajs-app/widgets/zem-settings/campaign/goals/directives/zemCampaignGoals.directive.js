angular.module('one.widgets').directive('zemCampaignGoals', function ($filter) {
    return {
        restrict: 'E',
        scope: {
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
            model: '=model',
            campaign: '=campaign',
            account: '=account',
            campaignGoals: '=goals',
            goalsDefaults: '=',
        },
        template: require('./zemCampaignGoals.directive.html'),
        controller: function ($uibModal, $scope) {
            $scope.campaignGoals = $scope.campaignGoals || [];
            $scope.i = 0;

            // Clear model
            $scope.model.added = [];
            $scope.model.modified = {};
            $scope.model.removed = [];
            $scope.model.primary = null;

            $scope.formatGoalValue = function (goal) {
                return $filter('campaignGoalText')(goal);
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
                scope.goalsDefaults = $scope.goalsDefaults;
                scope.campaign = $scope.campaign;
                scope.account = $scope.account;

                if (goal !== undefined) {
                    scope.campaignGoal = goal;
                }

                return $uibModal.open({
                    template: require('./zemEditCampaignGoalModal.partial.html'), // eslint-disable-line max-len
                    controller: 'zemEditCampaignGoalModalCtrl',
                    scope: scope,
                    backdrop: 'static',
                    keyboard: false,
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

            $scope.getKPIOptimizationLabel = function () {
                var label = '';
                for (var i = 0; i < $scope.campaignGoals.length; i++) {
                    var el = $scope.campaignGoals[i];
                    if (el.primary && constants.automaticallyOptimizedKPIGoals.indexOf(el.type) > -1) {
                        label = ('Goal ' + constants.campaignGoalValueText[el.type] +
                        ' is automatically optimized when data from Google Analytics/Adobe Analytics ' +
                        'is available and there are enough clicks for the data to be statistically significant.');
                        break;
                    }
                }
                return label;
            };

            $scope.getConversionPixelTag = function (name, url) {
                return '<!-- ' + name + '-->\n<img src="' + url + '" height="1" width="1" border="0" alt="" />';
            };

            $scope.copyConversionPixelTag = function (conversionGoal, $event) {
                // when clicking on Copy pixel prevent select primary goal
                var scope = $scope.$new(true);
                scope.conversionPixelTag = $scope.getConversionPixelTag(
                    conversionGoal.name, conversionGoal.pixelUrl);

                var modalInstance = $uibModal.open({
                    template: require('./zemCopyConversionPixelModal.partial.html'), // eslint-disable-line max-len
                    scope: scope,
                });
                modalInstance.result.then(function () {});

                $event.stopPropagation();
                return false;
            };

        },
    };
});
