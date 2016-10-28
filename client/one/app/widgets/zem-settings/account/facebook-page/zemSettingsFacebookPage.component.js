angular.module('one.widgets').component('zemSettingsFacebookPage', {
    bindings: {
        account: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/account/facebook-page/zemSettingsFacebookPage.component.html',
    controller: ['$q', '$uibModal', 'config', 'zemPermissions', function ($q, $uibModal, config, zemPermissions) {
        var $ctrl = this;

        $ctrl.config = config;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.clearFacebookPage = clearFacebookPage;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                canSave: canSave,
            });
        };

        $ctrl.$onChanges = function () {
            $ctrl.origFacebookPage = $ctrl.account.settings.facebookPage;
        };

        function clearFacebookPage () {
            $ctrl.account.settings.facebookPage = null;
            $ctrl.account.settings.facebookStatus = constants.facebookStatus.EMPTY;
        }

        function canSave () {
            if ($ctrl.origFacebookPage !== $ctrl.account.settings.facebookPage) {
                return askIfSave();
            }

            return $q.resolve();
        }

        function askIfSave () {
            var modal = $uibModal.open({
                templateUrl: '/partials/facebook_page_changed_modal.html',
                controller: ['$scope', function ($scope) {
                    $scope.ok = function () {
                        $scope.$close();
                    };

                    $scope.cancel = function () {
                        $scope.$dismiss('cancel');
                    };
                }],
                size: 'lg',
            });

            return modal.result;
        }

    }],
});
