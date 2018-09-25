angular.module('one.widgets').component('zemPublisherBidModifierUploadModal', {
    template: require('./zemPublisherBidModifierUploadModal.component.html'),
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    controller: function($scope, $q, $http, $window) {
        var $ctrl = this;

        $ctrl.isCreationMode = false;

        $ctrl.upsert = upsert;
        $ctrl.clearValidationError = clearValidationError;
        $ctrl.fileUploadCallback = fileUploadCallback;
        $ctrl.downloadErrors = downloadErrors;

        $ctrl.errors = {};
        $ctrl.putRequestInProgress = false;

        $ctrl.formData = {};

        function upsertReal(adGroupId, data) {
            var deferred = $q.defer();
            var url =
                '/rest/internal/adgroups/' +
                adGroupId +
                '/publishers/modifiers/upload/';

            var formData = new FormData();
            formData.append('file', data.file);

            $http
                .post(url, formData, {
                    transformRequest: angular.identity,
                    headers: {'Content-Type': undefined},
                })
                .then(function(data) {
                    deferred.resolve(data.data);
                })
                .catch(function(data) {
                    if (status === '413') {
                        data = {
                            data: {
                                errors: {
                                    entries: ['File too large (max 1MB).'],
                                },
                            },
                            success: false,
                        };
                    }
                    deferred.reject(data.data);
                });

            return deferred.promise;
        }

        function upsert() {
            $ctrl.putRequestInProgress = true;
            upsertReal($ctrl.resolve.adGroupId, $ctrl.formData)
                .then(function() {
                    $ctrl.modalInstance.close();
                })
                .catch(function(data) {
                    $ctrl.errors.entries = [data.details.file];
                    if (data.details.errorFileUrl) {
                        $ctrl.errors.errors_csv_key = data.details.errorFileUrl;
                    }
                })
                .finally(function() {
                    $ctrl.putRequestInProgress = false;
                });
        }

        function clearValidationError(field) {
            if (!$ctrl.errors) {
                return;
            }

            if ($ctrl.errors.hasOwnProperty(field)) {
                delete $ctrl.errors[field];
            }

            if (
                field === 'entries' &&
                $ctrl.errors.hasOwnProperty('errors_csv_key')
            ) {
                delete $ctrl.errors.errors_csv_key;
            }
        }

        function fileUploadCallback(file) {
            $ctrl.formData.file = file;
            $scope.$digest();
        }

        function downloadErrors() {
            var url =
                '/rest/internal/adgroups/' +
                $ctrl.resolve.adGroupId +
                '/publishers/modifiers/error_download/' +
                $ctrl.errors.errors_csv_key;
            $window.open(url, '_blank');
        }
    },
});
