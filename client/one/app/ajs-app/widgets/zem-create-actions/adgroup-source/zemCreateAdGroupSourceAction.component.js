angular.module('one.widgets').component('zemCreateAdGroupSourceAction', {
    template: require('./zemCreateAdGroupSourceAction.component.html'),
    bindings: {
        parentEntity: '<',
        isDisabled: '<',
    },
    controller: function(zemAdGroupSourcesStateService) {
        var $ctrl = this;
        $ctrl.checkDisabled = checkDisabled;

        $ctrl.$onInit = function() {
            $ctrl.stateService = zemAdGroupSourcesStateService.getInstance(
                $ctrl.parentEntity
            );
            $ctrl.stateService.initialize();
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.createAdGroupSource = createAdGroupSource;
        };

        function createAdGroupSource(sourceId) {
            if (!sourceId) return;
            $ctrl.stateService.create(sourceId);
        }

        function checkDisabled() {
            return $ctrl.isDisabled;
        }
    },
});
