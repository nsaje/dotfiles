/*globals angular*/
'use strict';

angular.module('one.legacy').controller('AccountCustomAudiencesCtrl', function ($scope, $state, $uibModal, api) { // eslint-disable-line max-len
    $scope.accountId = $state.params.id;
    $scope.audiencePixel = null;
    $scope.api = {
        refreshAudiences: undefined,
    };

    $scope.openAudienceModal = function () {
        var modal = $uibModal.open({
            component: 'zemCustomAudiencesModal',
            backdrop: 'static',
            keyboard: false,
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

    $scope.getAudiencePixel = function () {
        api.conversionPixel.list($scope.accountId, true).then(
            function (data) {
                if (data.rows) {
                    var audiencePixels = data.rows.filter(function (pixel) {
                        return pixel.audienceEnabled;
                    });

                    if (audiencePixels.length > 0) {
                        audiencePixels[0].id = audiencePixels[0].id.toString();
                        $scope.audiencePixel = audiencePixels[0];
                    }
                }
            },
            function (data) {
                return;
            }
        );
    };

    function init () {
        $scope.getAudiencePixel();
    }

    init();

    $scope.setActiveTab();
});
