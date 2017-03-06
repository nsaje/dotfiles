angular.module('one.widgets').component('zemCreateAdGroupSourceAction', {
    templateUrl: '/app/widgets/zem-create-actions/adgroup-source/zemCreateAdGroupSourceAction.component.html',
    bindings: {
        parentEntity: '<',
    },
    controller: function (zemAdGroupSourcesStateService) {
        var $ctrl = this;

        $ctrl.$onInit = function () {
            $ctrl.stateService = zemAdGroupSourcesStateService.getInstance($ctrl.parentEntity);
            $ctrl.stateService.initialize();
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.createAdGroupSource = createAdGroupSource;
        };

        function createAdGroupSource (sourceId) {
            if (!sourceId) return;
            $ctrl.stateService.create(sourceId);
        }
    },
});
