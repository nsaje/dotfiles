/* globals oneApp,options,constants,defaults */
oneApp.controller('EditCampaignGoalModalCtrl', ['$scope', '$modalInstance', 'api', function ($scope, $modalInstance, api) { // eslint-disable-line max-len
    $scope.conversionGoalTypes = options.conversionGoalTypes;
    $scope.conversionWindows = options.conversionWindows;
    $scope.campaignGoalKPIs = options.campaignGoalKPIs.filter($scope.$parent.isGoalAvailable);
    $scope.addConversionGoalInProgress = false;
    $scope.error = false;
    $scope.newCampaignGoal = false;
    $scope.unit = '';

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
        defaults.campaignGoalKPI.forEach(function (kpiDefault) {
            if (kpiDefault.id == $scope.campaignGoal.type) {
                defaultValue = kpiDefault.value;
            }
        });
        if (!$scope.newCampaignGoal) {
            return;
        }
        $scope.campaignGoal.value = defaultValue;
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
}]);
