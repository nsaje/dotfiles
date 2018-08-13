angular
    .module('one.views')
    .controller('zemArchivedView', function(zemNavigationNewService) {
        var $ctrl = this;

        init();

        function init() {
            $ctrl.entity = zemNavigationNewService.getActiveEntity();
            if ($ctrl.entity === undefined) {
                var handler = zemNavigationNewService.onActiveEntityChange(
                    function(event, entity) {
                        $ctrl.entity = entity;
                        handler();
                    }
                );
            }
        }
    });
