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
    }

    $scope.errors = {
        conversionGoal: {},
    };

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
            if (newGoal.id && newGoal.id === goal.id) {
                // skip same rows
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

    $scope.save = function () {
        $scope.clearErrors('type');
        $scope.clearErrors('value');

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
    $scope.campaignGoalKPIs = options.campaignGoalKPIs.filter($scope.isGoalAvailable);
    api.conversionPixel.list($scope.account.id).then(function (data) {
        $scope.availablePixels = data.rows;
        $scope.loadingPixels = false;
    });
}]);
