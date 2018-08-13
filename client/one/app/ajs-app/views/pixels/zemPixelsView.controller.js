angular
    .module('one.views')
    .controller('zemPixelsView', function(zemNavigationNewService) {
        var $ctrl = this;

        initialize();

        function initialize() {
            // WORKAROUND: Clear tab selection - not possible through uib API
            $('.uib-tab.active').removeClass('active');

            $ctrl.account = zemNavigationNewService.getActiveAccount();
            if (!$ctrl.account) {
                var handler = zemNavigationNewService.onActiveEntityChange(
                    function() {
                        $ctrl.account = zemNavigationNewService.getActiveAccount();
                        handler();
                    }
                );
            }
        }
    });
