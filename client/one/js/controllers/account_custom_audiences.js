/*globals angular*/
'use strict';

angular.module('one.legacy').controller('AccountCustomAudiencesCtrl', ['$scope', '$state', '$uibModal', function ($scope, $state, $uibModal) { // eslint-disable-line max-len
    $scope.accountId = $state.params.id;
    $scope.api = {
        refreshAudiences: undefined,
    };

    $scope.openAudienceModal = function () {
        var modal = $uibModal.open({
            component: 'zemCustomAudiencesModal',
            windowClass: 'modal-default',
            resolve: {
                accountId: function () {
                    return $scope.accountId;
                },
            },
        });

        modal.result.then(function () {
            if ($scope.api) {
                $scope.api.refreshAudiences();
            }
        });
    };

    $scope.setActiveTab();
}]);
