angular
    .module('one.services')
    .service('zemEntityActionsService', function(
        $http,
        $q,
        zemEntityActionsEndpoint,
        zemEntityBulkActionsEndpoint,
        zemPubSubService
    ) {
        // eslint-disable-line max-len

        function EntityActionsService(entityType) {
            var pubsub = zemPubSubService.createInstance();
            var level = getLevel(entityType);
            var parentLevel = getParentLevel(entityType);
            var breakdown = getBreakdown(entityType);

            var mapEntityActions = {};
            var mapEntityBulkActions = {};
            var mapSourceBulkActions = {};
            var mapPublisherBulkActions = {};
            var mapPlacementBulkActions = {};

            //
            // Public API
            //

            // Entity actions
            this.activate = createExecuteAction(
                constants.entityAction.ACTIVATE
            );
            this.deactivate = createExecuteAction(
                constants.entityAction.DEACTIVATE
            );
            this.archive = createExecuteAction(constants.entityAction.ARCHIVE);
            this.restore = createExecuteAction(constants.entityAction.RESTORE);
            this.clone = createExecuteAction(constants.entityAction.CLONE);

            // Bulk Entity actions
            this.activateEntities = createBulkExecuteAction(
                constants.entityAction.ACTIVATE,
                parentLevel,
                breakdown
            );
            this.deactivateEntities = createBulkExecuteAction(
                constants.entityAction.DEACTIVATE,
                parentLevel,
                breakdown
            );
            this.restoreEntities = createBulkExecuteAction(
                constants.entityAction.RESTORE,
                parentLevel,
                breakdown
            );
            this.archiveEntities = createBulkExecuteAction(
                constants.entityAction.ARCHIVE,
                parentLevel,
                breakdown
            );
            this.editEntities = createBulkExecuteAction(
                constants.entityAction.EDIT,
                parentLevel,
                breakdown
            );
            this.cloneEntities = createBulkExecuteAction(
                constants.entityAction.CLONE,
                parentLevel,
                breakdown
            );

            // Bulk Sources actions
            this.activateSources = createBulkExecuteAction(
                constants.entityAction.ACTIVATE,
                level,
                constants.breakdown.MEDIA_SOURCE
            );
            this.deactivateSources = createBulkExecuteAction(
                constants.entityAction.DEACTIVATE,
                level,
                constants.breakdown.MEDIA_SOURCE
            );

            this.getAction = getAction;
            this.onActionExecuted = onActionExecuted;

            //
            // Internal
            //
            var EVENTS = {
                ON_ENTITY_ACTION_EXECUTED: 'zem-entity-action-executed',
            };

            function getAction(actionType, action, breakdown) {
                if (actionType === constants.entityActionType.SINGLE)
                    return mapEntityActions[action];
                if (actionType === constants.entityActionType.BULK) {
                    if (breakdown === constants.breakdown.MEDIA_SOURCE) {
                        return mapSourceBulkActions[action];
                    } else if (breakdown === constants.breakdown.PUBLISHER) {
                        return mapPublisherBulkActions[action];
                    } else if (breakdown === constants.breakdown.PLACEMENT) {
                        return mapPlacementBulkActions[action];
                    }
                    return mapEntityBulkActions[action];
                }
            }

            function createExecuteAction(action) {
                var actionFn = function(id) {
                    var fn = getEndpointFn(action);
                    return fn(entityType, id).then(function(data) {
                        pubsub.notify(EVENTS.ON_ENTITY_ACTION_EXECUTED, {
                            action: action,
                            actionType: constants.entityActionType.SINGLE,
                            entityType: entityType,
                            entityId: id,
                            data: data,
                        });
                        return data;
                    });
                };

                mapEntityActions[action] = actionFn;
                return actionFn;
            }

            function createBulkExecuteAction(action, level, breakdown) {
                var actionFn = function(id, selection) {
                    var fn = getBulkEndpointFn(action);
                    return fn(level, breakdown, id, selection).then(function(
                        data
                    ) {
                        pubsub.notify(EVENTS.ON_ENTITY_ACTION_EXECUTED, {
                            action: action,
                            actionType: constants.entityActionType.BULK,
                            entityType: entityType,
                            level: level,
                            breakdown: breakdown,
                            entityId: id,
                            selection: selection,
                            data: data,
                        });
                        return data;
                    });
                };

                // Map actions
                if (breakdown === constants.breakdown.MEDIA_SOURCE) {
                    mapSourceBulkActions[action] = actionFn;
                } else if (breakdown === constants.breakdown.PUBLISHER) {
                    mapPublisherBulkActions[action] = actionFn;
                } else if (breakdown === constants.breakdown.PLACEMENT) {
                    mapPlacementBulkActions[action] = actionFn;
                } else {
                    mapEntityBulkActions[action] = actionFn;
                }

                return actionFn;
            }

            function getEndpointFn(action) {
                switch (action) {
                    case constants.entityAction.ACTIVATE:
                        return zemEntityActionsEndpoint.activate;
                    case constants.entityAction.DEACTIVATE:
                        return zemEntityActionsEndpoint.deactivate;
                    case constants.entityAction.ARCHIVE:
                        return zemEntityActionsEndpoint.archive;
                    case constants.entityAction.RESTORE:
                        return zemEntityActionsEndpoint.restore;
                }
            }

            function getBulkEndpointFn(action) {
                switch (action) {
                    case constants.entityAction.ACTIVATE:
                        return zemEntityBulkActionsEndpoint.activate;
                    case constants.entityAction.DEACTIVATE:
                        return zemEntityBulkActionsEndpoint.deactivate;
                    case constants.entityAction.ARCHIVE:
                        return zemEntityBulkActionsEndpoint.archive;
                    case constants.entityAction.RESTORE:
                        return zemEntityBulkActionsEndpoint.restore;
                    case constants.entityAction.EDIT:
                        return zemEntityBulkActionsEndpoint.edit;
                    case constants.entityAction.CLONE:
                        return zemEntityBulkActionsEndpoint.clone;
                }
            }

            //
            // Helper maps: entity -> level/breakdown maps (used by bulk actions)
            //
            function getParentLevel(entityType) {
                if (entityType === constants.entityType.ACCOUNT)
                    return constants.level.ALL_ACCOUNTS;
                if (entityType === constants.entityType.CAMPAIGN)
                    return constants.level.ACCOUNTS;
                if (entityType === constants.entityType.AD_GROUP)
                    return constants.level.CAMPAIGNS;
                if (entityType === constants.entityType.CONTENT_AD)
                    return constants.level.AD_GROUPS;
                throw Error('Unexpected entity type: ' + entityType);
            }

            function getLevel(entityType) {
                if (entityType === constants.entityType.ACCOUNT)
                    return constants.level.ACCOUNTS;
                if (entityType === constants.entityType.CAMPAIGN)
                    return constants.level.CAMPAIGNS;
                if (entityType === constants.entityType.AD_GROUP)
                    return constants.level.AD_GROUPS;
                if (entityType === constants.entityType.CONTENT_AD) return null;
                throw Error('Unexpected entity type: ' + entityType);
            }

            function getBreakdown(entityType) {
                if (entityType === constants.entityType.ACCOUNT)
                    return constants.breakdown.ACCOUNT;
                if (entityType === constants.entityType.CAMPAIGN)
                    return constants.breakdown.CAMPAIGN;
                if (entityType === constants.entityType.AD_GROUP)
                    return constants.breakdown.AD_GROUP;
                if (entityType === constants.entityType.CONTENT_AD)
                    return constants.breakdown.CONTENT_AD;
                throw Error('Unexpected entity type: ' + entityType);
            }

            //
            // Listener functionality
            //
            function onActionExecuted(callback) {
                return pubsub.register(
                    EVENTS.ON_ENTITY_ACTION_EXECUTED,
                    callback
                );
            }
        }

        return {
            createInstance: function(entityType) {
                return new EntityActionsService(entityType);
            },
        };
    });
