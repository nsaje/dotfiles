/*globals oneApp,constants,options,moment*/
oneApp.controller('AccountReportsCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.reports = [];
    $scope.requestInProgress = false;

    $scope.getReports = function() {
        $scope.requestInProgress = true;

        api.accountReports.get($state.params.id).then(
            function (data) {
                $scope.reports = data.reports;
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.removeReport = function(scheduledReportId) {
      $scope.requestInProgress = true;

      api.accountReports.removeReport(scheduledReportId).then(
          function (data) {
              $scope.getReports();
          },
          function (data) {
              // error
              return;
          }
      ).finally(function () {
          $scope.requestInProgress = false;
      });
    };

    $scope.getReports();

}]);
