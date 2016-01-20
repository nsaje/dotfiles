/* globals oneApp,options */
oneApp.controller('AddConversionGoalModalCtrl', ['$scope', '$modalInstance', 'api', function ($scope, $modalInstance, api) {
    $scope.conversionGoalTypes = options.conversionGoalTypes;
    $scope.conversionWindows = options.conversionWindows;
    $scope.addConversionGoalInProgress = false;
    $scope.error = false;

    $scope.conversionGoal = {};
    $scope.errors = {};

    $scope.addConversionGoal = function () {
        $scope.addConversionGoalInProgress = true;
        $scope.error = false;
        api.conversionGoal.post($scope.campaign.id, $scope.conversionGoal).then(
            function () {
                $modalInstance.close();
            },
            function (errors) {
                if (errors) {
                    $scope.errors = errors;
                } else {
                    $scope.error = true;
                }
            }
        ).finally(function () {
            $scope.addConversionGoalInProgress = false;
        });
    };

    $scope.clearErrors = function (name) {
        if (!$scope.errors) {
            return;
        }
        delete $scope.errors[name];
    };

    $scope.showConversionPixelForm = function () {
        return $scope.conversionGoal.type === constants.conversionGoalType.PIXEL;
    };

    $scope.showGAForm = function () {
        return $scope.conversionGoal.type === constants.conversionGoalType.GA;
    };

    $scope.showOmnitureForm = function () {
        return $scope.conversionGoal.type === constants.conversionGoalType.OMNITURE;
    };

    $scope.updateTypeChange = function () {
        delete $scope.conversionGoal.goalId;
        delete $scope.conversionGoal.conversionWindow;

        $scope.clearErrors('type');
        $scope.clearErrors('conversionWindow');
        $scope.clearErrors('goalId');
    };
}]);
