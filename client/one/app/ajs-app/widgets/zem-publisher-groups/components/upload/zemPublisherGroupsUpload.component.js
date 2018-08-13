angular.module('one.widgets').component('zemPublisherGroupsUpload', {
    template: require('./zemPublisherGroupsUpload.component.html'),
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    controller: function($scope, zemPublisherGroupsEndpoint) {
        var $ctrl = this;

        $ctrl.isCreationMode = false;

        $ctrl.upsert = upsert;
        $ctrl.clearValidationError = clearValidationError;
        $ctrl.fileUploadCallback = fileUploadCallback;
        $ctrl.downloadErrors = downloadErrors;
        $ctrl.downloadExample = downloadExample;

        $ctrl.errors = null;
        $ctrl.putRequestInProgress = false;

        $ctrl.$onInit = function() {
            $ctrl.formData = {};
            if ($ctrl.resolve.publisherGroup) {
                $ctrl.formData = {
                    id: $ctrl.resolve.publisherGroup.id,
                    name: $ctrl.resolve.publisherGroup.name,
                    include_subdomains:
                        $ctrl.resolve.publisherGroup.include_subdomains,
                };
            }
            if (!$ctrl.formData.id) {
                $ctrl.isCreationMode = true;
                $ctrl.formData.include_subdomains = true;
            }
        };

        function upsert() {
            $ctrl.putRequestInProgress = true;
            zemPublisherGroupsEndpoint
                .upsert($ctrl.resolve.account.id, $ctrl.formData)
                .then(function() {
                    $ctrl.modalInstance.close();
                })
                .catch(function(data) {
                    $ctrl.errors = data;
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
            zemPublisherGroupsEndpoint.downloadErrors(
                $ctrl.resolve.account.id,
                $ctrl.errors.errors_csv_key
            );
        }

        function downloadExample() {
            zemPublisherGroupsEndpoint.downloadExample();
        }
    },
});
