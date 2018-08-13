angular
    .module('one.views')
    .controller('zemCampaignLauncherView', function(zemNavigationNewService) {
        var $ctrl = this;

        initialize();

        function initialize() {
            var activeEntity = zemNavigationNewService.getActiveEntity();
            if (activeEntity === undefined) {
                var handler = zemNavigationNewService.onActiveEntityChange(
                    function() {
                        $ctrl.account = zemNavigationNewService.getActiveAccount();
                        handler();
                    }
                );
            } else {
                $ctrl.account = zemNavigationNewService.getActiveAccount();
            }
        }
    });
