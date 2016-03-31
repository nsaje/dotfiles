/* globals oneApp,options,constants,defaults,angular */
oneApp.controller('EditCampaignGoalModalCtrl', ['$scope', '$modalInstance', 'api', function ($scope, $modalInstance, api) { // eslint-disable-line max-len
    $scope.conversionGoalTypes = options.conversionGoalTypes;
    $scope.conversionWindows = options.conversionWindows;
    $scope.addConversionGoalInProgress = false;
    $scope.error = false;
    $scope.newCampaignGoal = false;
    $scope.unit = '';
    $scope.availablePixels = [];
    $scope.loadingPixels = true;

    if ($scope.campaignGoal === undefined) {
        $scope.newCampaignGoal = true;
        $scope.campaignGoal = {
            primary: false,
            conversionGoal: {},
        };
    } else {
        options.campaignGoalKPIs.forEach(function (kpiDefault) {
            if (kpiDefault.value === $scope.campaignGoal.type) {
                $scope.unit = kpiDefault.unit;
            }
        });
    }

    $scope.errors = {
        conversionGoal: {},
    };


    function getTypeId (goal) {
        if (goal.conversionGoal.type !== constants.conversionGoalType.PIXEL) {
            return goal.conversionGoal.type + '::' + goal.conversionGoal.goalId;
        }
        return [
            goal.conversionGoal.type,
            goal.conversionGoal.goalId,
            goal.conversionGoal.conversionWindow,
        ].join('::');
    }

    $scope.setDefaultValue = function () {
        var defaultValue = null;
        if (!$scope.newCampaignGoal) {
            return;
        }
        defaults.campaignGoalKPI.forEach(function (kpiDefault) {
            if (kpiDefault.id === $scope.campaignGoal.type) {
                defaultValue = kpiDefault.value;
            }
        });

        $scope.campaignGoal.value = defaultValue;
    };

    $scope.isGoalAvailable = function (option) {
        var isAvailable = true,
            goal = $scope.campaignGoal,
            countConversionGoals = 0;
        if (!goal || goal && goal.type === option.value) {
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

    $scope.validate = function (newGoal, allErrors) {
        var goalTypeIds = {},
            goalNames = {},
            errors = {};

        if (!$scope.newCampaignGoal) {
            return true;
        }

        if (newGoal.type !== constants.campaignGoalKPI.CPA) {
            return true;
        }

        goalNames[newGoal.conversionGoal.name] = 1;
        goalTypeIds[
            getTypeId(newGoal)
        ] = 1;

        $scope.campaignGoals.forEach(function (goal) {
            if (goal.type !== constants.campaignGoalKPI.CPA) {
                return;
            }
            if (newGoal.id && newGoal.id === goal.id) {
                // skip same rows
                return;
            }
            var typeId = getTypeId(goal);
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

    $scope.save = function () {
        $scope.clearErrors('type');
        $scope.clearErrors('value');

        $scope.campaignGoal.value = Math.abs($scope.campaignGoal.value);

        if (!$scope.newCampaignGoal) {
            $modalInstance.close($scope.campaignGoal);
            return; // Skip server validation call if this is not a new entry
        }

        if (!$scope.validate($scope.campaignGoal, $scope.errors)) {
            return;
        }

        api.campaignGoalValidation.post(
            $scope.campaign.id,
            $scope.campaignGoal
        ).then(function () {
            $modalInstance.close($scope.campaignGoal);
        }, function (response) {
            $scope.errors = api.campaignGoalValidation.convert.errorsFromApi(response);
        });

    };

    $scope.clearErrors = function (name) {
        if (!$scope.errors) {
            return;
        }
        delete $scope.errors[name];
    };

    $scope.showAddConversionGoalForm = function () {
        return $scope.campaignGoal.type === constants.campaignGoalKPI.CPA;
    };

    $scope.showConversionPixelForm = function () {
        return $scope.campaignGoal.conversionGoal.type === constants.conversionGoalType.PIXEL;
    };

    $scope.showGAForm = function () {
        return $scope.campaignGoal.conversionGoal.type === constants.conversionGoalType.GA;
    };

    $scope.showOmnitureForm = function () {
        return $scope.campaignGoal.conversionGoal.type === constants.conversionGoalType.OMNITURE;
    };

    $scope.updateTypeChange = function (unit) {
        delete $scope.campaignGoal.conversionGoal.goalId;
        delete $scope.campaignGoal.conversionGoal.conversionWindow;

        $scope.clearErrors('type');
        $scope.clearErrors('conversionGoal');

        $scope.setDefaultValue();
        $scope.unit = unit || '';
    };

    $scope.prepareName = function (option) {
        if ($scope.newCampaignGoal) {
            return option && option.name || undefined;
        }
        if ($scope.campaignGoal.type !== constants.campaignGoalKPI.CPA) {
            return option.name;
        }
        return 'CPA - ' + $scope.campaignGoal.conversionGoal.name;
    };

    $scope.campaignGoalKPIs = options.campaignGoalKPIs.filter($scope.isGoalAvailable);


    $scope.refreshConversionWindows = function (goalId) {
        var counts = {};
        $scope.conversionWindows = [];
        $scope.campaignGoals.forEach(function (goal) {
            if (goal.type !== constants.campaignGoalKPI.CPA) {
                return;
            }
            if (goal.conversionGoal.goalId === goalId) {
                if (!counts[goal.conversionGoal.conversionWindow]) {
                    counts[goal.conversionGoal.conversionWindow] = 0;
                }
                counts[goal.conversionGoal.conversionWindow]++;
            }
        });
        options.conversionWindows.forEach(function (opt) {
            if (!counts[opt.value]) {
                $scope.conversionWindows.push(opt);
            }
        });
    };


    api.conversionPixel.list($scope.account.id).then(function (data) {
        $scope.availablePixels = data.rows;
        $scope.loadingPixels = false;
    });
}]);

