require('./zemDemoRequest.component.less');

angular.module('one.widgets').component('zemDemoRequest', {
    bindings: {
        modalInstance: '<',
    },
    template: require('./zemDemoRequest.component.html'),
    controller: function(zemDemoRequestService) {
        var $ctrl = this;

        $ctrl.$onInit = function() {
            $ctrl.requestInProgress = true;
            zemDemoRequestService
                .requestDemo()
                .then(function(data) {
                    $ctrl.demoUrl = data.url;
                    $ctrl.demoPassword = data.password;
                })
                .catch(function(errorMessage) {
                    $ctrl.error = true;
                    $ctrl.errorMessage = errorMessage;
                })
                .finally(function() {
                    $ctrl.requestInProgress = false;
                });

            if ($ctrl.modalInstance) {
                // If zemDemoRequest was initialized inside $uibModal add funciton to controller to close the modal
                $ctrl.closeModal = $ctrl.modalInstance.close;
            }
        };
    },
});
