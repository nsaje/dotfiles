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
        zemAuthStore,
        zemUtils,
        $location,
        $window,
        zemEntitiesUpdatesService
    ) {
        var $ctrl = this;
        $ctrl.hasPermission = zemAuthStore.hasPermission.bind(zemAuthStore);
        $ctrl.openHistory = openHistory;

        var entityUpdateHandler;
        var actionExecutedHandler;
        var dateRangeUpdateHandler;
        var dataFilterUpdateHandler;
        var activeEntityChangeHandler;
        var bidModifierUpdateHandler;
        var entitiesUpdates$;

        var legacyActiveEntityUpdateHandler;
        var legacyEntityUpdateHandler;
        var legacyActionExecutedHandler;

        $ctrl.$onInit = function() {
            dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(
                reloadInfoboxData
            );
            dataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(
                reloadInfoboxData
            );
            bidModifierUpdateHandler = zemNavigationNewService.onBidModifierUpdate(
                reloadInfoboxData
            );
            entitiesUpdates$ = zemEntitiesUpdatesService
                .getAllUpdates$()
                .subscribe(function(entityUpdate) {
                    if (entityUpdate.action === constants.entityAction.EDIT) {
                        reloadInfoboxData();
                    }
                });
        };

        $ctrl.$onChanges = function(changes) {
            if (changes.entity) {
                onEntityUpdated();

                if (entityUpdateHandler) entityUpdateHandler();
                if (actionExecutedHandler) actionExecutedHandler();

                if ($ctrl.entity) {
                    entityUpdateHandler = zemEntityService
                        .getEntityService($ctrl.entity.type)
                        .onEntityUpdated(onEntityUpdated);
                    actionExecutedHandler = zemEntityService
                        .getEntityService($ctrl.entity.type)
                        .onActionExecuted(onActionExecuted);
                }
            }
        };

        // eslint-disable-next-line complexity
        $ctrl.$onDestroy = function() {
            if (entityUpdateHandler) entityUpdateHandler();
            if (actionExecutedHandler) actionExecutedHandler();
            if (dateRangeUpdateHandler) dateRangeUpdateHandler();
            if (dataFilterUpdateHandler) dataFilterUpdateHandler();
            if (activeEntityChangeHandler) activeEntityChangeHandler();
            if (bidModifierUpdateHandler) bidModifierUpdateHandler();
            if (entitiesUpdates$) entitiesUpdates$.unsubscribe();

            if (legacyActiveEntityUpdateHandler)
                legacyActiveEntityUpdateHandler();
            if (legacyEntityUpdateHandler) legacyEntityUpdateHandler();
            if (legacyActionExecutedHandler) legacyActionExecutedHandler();
        };

        function onEntityUpdated() {
            updateEntity();
            reloadInfoboxData();
        }

        function onActionExecuted(event, actionData) {
            updateEntity(actionData.data.data.state);
            reloadInfoboxData();
        }

        function updateEntity(updatedEntityState) {
            if (updatedEntityState) {
                // Update entity's state immediately after action is executed to
                // show consistent state in infobox even when navigation load is
                // not yet finished
                $ctrl.entity.data.state = updatedEntityState;
            }
        }

        function reloadInfoboxData() {
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
