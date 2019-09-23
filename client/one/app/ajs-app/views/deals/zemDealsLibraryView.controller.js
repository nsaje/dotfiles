angular
    .module('one.views')
    .controller('zemDealsLibraryView', function(zemNavigationNewService) {
        var $ctrl = this;

        initialize();

        function initialize() {
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
