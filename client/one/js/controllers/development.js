/*globals oneApp*/

oneApp.controller('DevelopmentCtrl', ['$scope', '$state', function ($scope, $state) {
    $scope.$on('$stateChangeSuccess',
      function(event, toState, toParams, fromState, fromParams){
          // TODO: check permission
    });
}]);
