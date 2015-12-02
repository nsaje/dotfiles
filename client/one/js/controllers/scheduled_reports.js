/*globals oneApp,constants,options,moment*/
oneApp.controller('ScheduledReportsCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.reports = [];
    $scope.requestInProgress = false;
    $scope.errorMessage = '';

    $scope.getReports = function() {
        $scope.requestInProgress = true;

        api.scheduledReports.get($scope.level, $state.params.id).then(
            function (data) {
                $scope.reports = data.reports;
                $scope.errorMessage = '';
            },
            function (data) {
                // error
                $scope.errorMessage = 'Error Retrieving Reports';
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.removeReport = function(scheduledReportId) {
      $scope.requestInProgress = true;

      api.scheduledReports.removeReport(scheduledReportId).then(
          function (data) {
              $scope.errorMessage = '';
              $scope.getReports();
          },
          function (data) {
              // error
              $scope.errorMessage = 'Error Removing Report. Please contact support.';
              $scope.requestInProgress = false;
              return;
          }
      );
    };

    $scope.getReports();

}]);
