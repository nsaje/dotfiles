/* globals oneApp,options,constants */
oneApp.controller('EditCampaignGoalModalCtrl',
                  ['$scope', '$modalInstance', function ($scope, $modalInstance) {
                      $scope.conversionGoalTypes = options.conversionGoalTypes;
                      $scope.conversionWindows = options.conversionWindows;
                      $scope.campaignGoalKPIs = options.campaignGoalKPIs;
                      $scope.addConversionGoalInProgress = false;
                      $scope.error = false;
                      $scope.newCampaignGoal = false;

                      if ($scope.campaignGoal === undefined) {
                          $scope.newCampaignGoal = true;
                          $scope.campaignGoal = {
                              primary: false,
                              conversionGoal: {},
                          };
                      }

                      $scope.errors = {};

                      $scope.save = function () {
                          $modalInstance.close($scope.campaignGoal);
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

                      $scope.updateTypeChange = function () {
                          delete $scope.campaignGoal.conversionGoal.goalId;
                          delete $scope.campaignGoal.conversionGoal.conversionWindow;

                          $scope.clearErrors('type');
                          $scope.clearErrors('conversionWindow');
                          $scope.clearErrors('goalId');
                      };
                  }]);
