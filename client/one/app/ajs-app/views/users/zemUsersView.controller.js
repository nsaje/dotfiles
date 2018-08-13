angular
    .module('one.views')
    .controller('zemUsersView', function(zemNavigationNewService) {
        var $ctrl = this;

        initialize();

        function initialize() {
            // WORKAROUND: Clear tab selection - not possible through uib API
            $('.uib-tab.active').removeClass('active');

            $ctrl.entity = zemNavigationNewService.getActiveEntity();
            if (!$ctrl.entity) {
                var handler = zemNavigationNewService.onActiveEntityChange(
                    function() {
                        $ctrl.entity = zemNavigationNewService.getActiveEntity();
                        handler();
                    }
                );
            }
        }
    });
