angular.module('one.widgets').component('zemInfobox', {
    templateUrl: '/app/widgets/zem-infobox/zemInfobox.component.html',
    controller: function (zemInfoboxService, zemNavigationNewService, zemDataFilterService, zemEntityService) {
        var $ctrl = this;

        var activeEntityUpdateHandler;
        var hierarchyUpdateHandler;
        var dateRangeUpdateHandler;
        var dataFilterUpdateHandler;

        $ctrl.$onInit = function () {
            var entityUpdateHandler;

            updateHandler();

            activeEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(function (event, activeEntity) {
                if (entityUpdateHandler) {
                    // Unsubscribe from updates on previous entity
                    entityUpdateHandler();
                }
                if (activeEntity) {
                    // Subscribe to updates on current entity
                    entityUpdateHandler = zemEntityService.getEntityService(activeEntity.type).onEntityUpdated(
                        updateHandler
                    );
                }
                updateHandler();
            });
            hierarchyUpdateHandler = zemNavigationNewService.onHierarchyUpdate(updateHandler);
            dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(updateHandler);
            dataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(updateHandler);
        };

        $ctrl.$onDestroy = function () {
            // FIXME: Calling activeEntityUpdateHandler doesn't unsubscribe component from
            // zemNavigationNewService.onActiveEntityChange immediately but only after another view change. Probably
            // onActiveEntityChange callback is triggered before component is destroyed.
            activeEntityUpdateHandler();
            hierarchyUpdateHandler();
            dateRangeUpdateHandler();
            dataFilterUpdateHandler();
        };

        function updateHandler () {
            zemInfoboxService.reloadInfoboxData(zemNavigationNewService.getActiveEntity()).then(updateView);
        }

        function updateView (data) {
            if (!data) {
                delete $ctrl.entity;
                delete $ctrl.delivery;
                delete $ctrl.basicSettings;
                delete $ctrl.performanceSettings;
                return;
            }

            $ctrl.entity = zemNavigationNewService.getActiveEntity();
            $ctrl.delivery = data.delivery;
            $ctrl.basicSettings = data.basicSettings;
            $ctrl.performanceSettings = data.performanceSettings;
        }
    },
});
