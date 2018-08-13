angular
    .module('one.views')
    .controller('zemAccountCreditView', function(zemNavigationNewService) {
        var $ctrl = this;

        init();

        function init() {
            // WORKAROUND: Clear tab selection - not possible through uib API
            $('.uib-tab.active').removeClass('active');

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
