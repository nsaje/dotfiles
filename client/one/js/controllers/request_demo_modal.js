/* globals angular */
angular.module('one.legacy').controller('RequestDemoModalCtrl', ['$scope', 'api', function ($scope, api) {

    $scope.inProgress = true;
    $scope.error = false;

    api.demo.request().then(
        function (data) {
            $scope.inProgress = false;
            $scope.url = data.data.data.url;
            $scope.password = data.data.data.password;
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
        $scope.$close();
    };
}]);
