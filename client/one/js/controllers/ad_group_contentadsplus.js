/* globals oneApp */
oneApp.controller('AdGroupAdsPlusCtrl', ['$scope', '$modal', function ($scope, $modal) {
    $scope.addContentAds = function() {
        var modalInstance = $modal.open({
            templateUrl: '/partials/upload_ads_modal.html',
            controller: 'UploadAdsModalCtrl',
            windowClass: 'upload-ads-modal',
            scope: $scope
        });

        return modalInstance;
    };
}]);
