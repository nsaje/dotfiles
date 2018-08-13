require('./zemInfobox.component.less');

angular.module('one.widgets').component('zemInfobox', {
    bindings: {
        entity: '<',
    },
    template: require('./zemInfobox.component.html'),
    controller: function(
        zemInfoboxService,
        zemNavigationNewService,
        zemDataFilterService,
        zemEntityService,
        zemHistoryService,
        zemPermissions,
        zemUtils,
        $state,
        $location,
        $window
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.openHistory = openHistory;

        var entityUpdateHandler;
        var actionExecutedHandler;
        var dateRangeUpdateHandler;
        var dataFilterUpdateHandler;

        var legacyActiveEntityUpdateHandler;
        var legacyEntityUpdateHandler;
        var legacyActionExecutedHandler;

        $ctrl.$onInit = function() {
            if (!$state.includes('v2.analytics')) {
                $ctrl.entity = zemNavigationNewService.getActiveEntity();
                updateHandler();
                if ($ctrl.entity) {
                    legacyEntityUpdateHandler = zemEntityService
                        .getEntityService($ctrl.entity.type)
                        .onEntityUpdated(updateHandler);
                    legacyActionExecutedHandler = zemEntityService
                        .getEntityService($ctrl.entity.type)
                        .onActionExecuted(updateHandler);
                }

                legacyActiveEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(
                    function(event, activeEntity) {
                        if (legacyEntityUpdateHandler)
                            legacyEntityUpdateHandler();
                        if (legacyActionExecutedHandler)
                            legacyActionExecutedHandler();

                        $ctrl.entity = activeEntity;
                        updateHandler();
                        if (activeEntity) {
                            legacyEntityUpdateHandler = zemEntityService
                                .getEntityService($ctrl.entity.type)
                                .onEntityUpdated(updateHandler);
                            legacyActionExecutedHandler = zemEntityService
                                .getEntityService($ctrl.entity.type)
                                .onActionExecuted(updateHandler);
                        }
                    }
                );
            }

            dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(
                updateHandler
            );
            dataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(
                updateHandler
            );
        };

        $ctrl.$onChanges = function(changes) {
            if ($state.includes('v2.analytics')) {
                $ctrl.entity = changes.entity.currentValue;
                updateHandler();
                if ($ctrl.entity) {
                    if (entityUpdateHandler) entityUpdateHandler();
                    entityUpdateHandler = zemEntityService
                        .getEntityService($ctrl.entity.type)
                        .onEntityUpdated(updateHandler);
                    if (actionExecutedHandler) actionExecutedHandler();
                    actionExecutedHandler = zemEntityService
                        .getEntityService($ctrl.entity.type)
                        .onActionExecuted(updateHandler);
                }
            }
        };

        $ctrl.$onDestroy = function() {
            if (entityUpdateHandler) entityUpdateHandler();
            if (actionExecutedHandler) actionExecutedHandler();
            if (dateRangeUpdateHandler) dateRangeUpdateHandler();
            if (dataFilterUpdateHandler) dataFilterUpdateHandler();

            if (legacyActiveEntityUpdateHandler)
                legacyActiveEntityUpdateHandler();
            if (legacyEntityUpdateHandler) legacyEntityUpdateHandler();
            if (legacyActionExecutedHandler) legacyActionExecutedHandler();
        };

        function updateHandler() {
            $ctrl.loadRequestInProgress = true;
            zemInfoboxService
                .reloadInfoboxData($ctrl.entity)
                .then(updateView)
                .finally(function() {
                    $ctrl.loadRequestInProgress = false;
                });
        }

        function updateView(data) {
            if (!data) {
                delete $ctrl.entity;
                delete $ctrl.isEntityAvailable;
                delete $ctrl.delivery;
                delete $ctrl.basicSettings;
                delete $ctrl.performanceSettings;
                return;
            }

            $ctrl.entity = zemNavigationNewService.getActiveEntity();
            $ctrl.isEntityAvailable = $ctrl.entity ? true : false;
            $ctrl.delivery = data.delivery;
            $ctrl.basicSettings = data.basicSettings;
            $ctrl.performanceSettings = data.performanceSettings;
        }

        function openHistory(event) {
            if (zemUtils.shouldOpenInNewTab(event)) {
                openInNewTabWithParam(zemHistoryService.QUERY_PARAM);
            } else {
                zemHistoryService.open();
            }
        }

        function openInNewTabWithParam(param) {
            var tempLocation = angular.copy($location);
            tempLocation.search(param, true);
            $window.open(tempLocation.absUrl(), '_blank');
        }
    },
});
