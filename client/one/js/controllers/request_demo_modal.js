/* globals oneApp */
oneApp.controller('RequestDemoModalCtrl', ['$scope', '$modalInstance', 'api', function ($scope, $modalInstance, api) {

    $scope.inProgress = true;
    $scope.error = false;

    api.demo.request().then(
        function (data) {
            $scope.inProgress = false;
            $scope.url = data.data.data;
        },
        function (data) {
            $scope.inProgress = false;
            $scope.error = true;
            if (data && data.message) {
                $scope.errorMessage = data.message;
            }
        }
    );

    $scope.close = function () {
        $modalInstance.close();
    };
}]);
