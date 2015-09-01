/* globals angular,oneApp,defaults */
oneApp.controller('UploadAdsModalCtrl', ['$scope', '$modalInstance', 'api', '$state', '$timeout', '$filter', function($scope, $modalInstance, api, $state, $timeout, $filter) {
    $scope.errors = null;
    $scope.formData = {};

    $scope.callToActionSelect2Config = {
        dropdownCssClass: 'service-fee-select2',
        createSearchChoice: function (term, data) {
            if ($(data).filter(function() { 
                return this.text.localeCompare(term)===0;
            }).length===0) {
                return {id: term, text: term};
            }
        },
        data: defaults.callToAction
    };

    $scope.pollBatchStatus = function(batchId) {
        if ($scope.isInProgress) {
            $timeout(function() {
                api.adGroupAdsPlusUpload.checkStatus($state.params.id, batchId).then(
                    function(data) {
                        if (data.status === constants.uploadBatchStatus.DONE) {
                            $scope.isInProgress = false;
                            $modalInstance.close();
                        } else if (data.status === constants.uploadBatchStatus.FAILED) {
                            $scope.isInProgress = false;
                            $scope.errors = data.errors;
                        }
                        $scope.countUploaded = data.count;
                        $scope.countAll = data.all;
                    },
                    function(data) {
                        $scope.isInProgress = false;
                    }
                ).finally(function() {
                    $scope.pollBatchStatus(batchId);
                });
            }, 1000);
        }
    };

    var replaceStart = /^https?:\/\//;
    var replaceEnd = /\/$/;
    function cleanDisplayUrl(data) {
        if(data.displayUrl === undefined) {
            return;
        }

        data.displayUrl = data.displayUrl.replace(replaceStart,'');
        data.displayUrl = data.displayUrl.replace(replaceEnd, '');
    };

    $scope.clearErrors = function(name) {
        if (!$scope.errors) {
            return;
        }
        delete $scope.errors[name];
    };

    $scope.upload = function() {
        if ($scope.isInProgress) {
            return;
        }

        $scope.isInProgress = true;
        $scope.countUploaded = 0;
        $scope.countAll = 0;
        $scope.errors = null;        

        cleanDisplayUrl($scope.formData);

        api.adGroupAdsPlusUpload.upload(
            $state.params.id, $scope.formData
        ).then(function(batchId) {
            $scope.pollBatchStatus(batchId);

            $scope.remindToAddBudget.resolve(true);
        }, function(data) {
            $scope.isInProgress = false;
            $scope.countUploaded = 0;
            $scope.countAll = 0;
            $scope.errors = data.errors;
        });
    };

    $scope.init = function() {
        api.adGroupAdsPlusUpload.getDefaults($state.params.id).then(
            function(data) {
                angular.extend($scope.formData, data.defaults);
                $scope.formData.batchName = '';
            });
    };

    $scope.$watch('formData.file', function (newValue, oldValue) {
        if ($scope.formData.batchName !== '') { return; }
        if (! newValue) { return; }
        $scope.formData.batchName = newValue.name;
    });

    $scope.init();
}]);
