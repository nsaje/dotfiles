angular.module('one.widgets').component('zemFacebookPageSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemFacebookPageSettings.component.html'),
    controller: function($q, $uibModal, config, zemPermissions) {
        var $ctrl = this;

        $ctrl.config = config;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.clearFacebookPage = clearFacebookPage;

        $ctrl.$onInit = function() {
            $ctrl.api.register({
                validate: validate,
            });
        };

        $ctrl.$onChanges = function() {
            if (!$ctrl.entity) return;
            $ctrl.origFacebookPage = $ctrl.entity.settings.facebookPage;
        };

        function clearFacebookPage() {
            $ctrl.entity.settings.facebookPage = null;
            $ctrl.entity.settings.facebookStatus =
                constants.facebookStatus.EMPTY;
        }

        function validate() {
            if ($ctrl.origFacebookPage !== $ctrl.entity.settings.facebookPage) {
                return askIfSave();
            }

            return $q.resolve();
        }

        function askIfSave() {
            var modal = $uibModal.open({
                template: require('./partials/facebook_page_changed_modal.html'),
                backdrop: 'static',
                keyboard: false,
                controller: function($scope) {
                    $scope.ok = function() {
                        $scope.$close();
                    };

                    $scope.cancel = function() {
                        $scope.$dismiss('cancel');
                    };
                },
                size: 'lg',
            });

            return modal.result;
        }
    },
});
