require('./zemCustomAudiences.component.less');

angular.module('one.widgets').component('zemCustomAudiences', {
    template: require('./zemCustomAudiences.component.html'),
    bindings: {
        account: '<',
    },
    controller: function(
        $scope,
        $uibModal,
        zemAuthStore,
        zemCustomAudiencesStateService
    ) {
        var $ctrl = this;
        $ctrl.hasPermission = zemAuthStore.hasPermission.bind(zemAuthStore);
        $ctrl.isPermissionInternal = zemAuthStore.isPermissionInternal.bind(
            zemAuthStore
        );

        $ctrl.tooltipText = tooltipText;
        $ctrl.openAudienceModal = openAudienceModal;

        $ctrl.$onInit = function() {
            $ctrl.stateService = zemCustomAudiencesStateService.getInstance(
                $ctrl.account
            );
            $ctrl.stateService.initialize();
            $ctrl.state = $ctrl.stateService.getState();
        };

        $ctrl.$onDestroy = function() {
            $ctrl.stateService.destroy();
        };

        $scope.$on('pixelAudienceEnabled', function() {
            // FIXME: avoid broadcast in pixelAudienceEnabled propagation
            // Broadcasted to notify that custom Audience can be created
            $ctrl.stateService.listAudiencePixels();
        });

        function openAudienceModal() {
            if (!$ctrl.state.audiencePixels[0]) {
                return;
            }

            $uibModal.open({
                component: 'zemCustomAudiencesModal',
                backdrop: 'static',
                keyboard: false,
                resolve: {
                    stateService: $ctrl.stateService,
                },
            });
        }

        function tooltipText() {
            if (!$ctrl.state.audiencePixels[0]) {
                return (
                    'Please first define the pixel to build custom audiences from. ' +
                    'If you already have the pixel created there, click Edit and set it as audience building pixel.'
                );
            }
            return '';
        }
    },
});
