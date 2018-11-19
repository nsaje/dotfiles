require('./zemCampaignLauncherObjectives.component.less');

angular.module('one').component('zemCampaignLauncherObjectives', {
    bindings: {
        stateService: '=',
    },
    template: require('./zemCampaignLauncherObjectives.component.html'), // eslint-disable-line max-len
    controller: function(zemPermissions) {
        var $ctrl = this;
        $ctrl.selectObjective = selectObjective;
        $ctrl.hasPermission = zemPermissions.hasPermission;

        $ctrl.$onInit = function() {
            $ctrl.state = $ctrl.stateService.getState();
        };

        function selectObjective(objective) {
            $ctrl.stateService.initLauncherWithObjective(objective);
        }
    },
});
