oneActionLogApp.controller('ActionLogCtrl', ['$scope', '$state', '$location', 'api', function ($scope, $state, $location, api) {

    $scope.user = null;
    $scope.actionLog = null;

    api.actionLog.get().then(function (data) {
        $scope.actionLog = data;
        console.log(data);
    });

}]);
