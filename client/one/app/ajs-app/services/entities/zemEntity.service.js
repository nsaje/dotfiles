angular
    .module('one.services')
    .service('zemEntityService', function(
        $http,
        $q,
        zemAccountService,
        zemCampaignService,
        zemAdGroupService,
        zemContentAdService
    ) {
        // eslint-disable-line max-len
        // zemEntityService - Helper for manipulating entities and executing actions
        // It provides standard methods (get/update/create) and actions (bulk) that are bridged to specific entity service

        //
        // Public API
        //
        this.getEntity = getEntity;
        this.createEntity = createEntity;
        this.cloneEntity = cloneEntity;
        this.updateEntity = updateEntity;
        this.getEntityService = getEntityService;
        this.executeAction = executeAction;
        this.executeBulkAction = executeBulkAction;

        function getEntity(entityType, id) {
            return getEntityService(entityType).get(id);
        }

        function updateEntity(entityType, id, data) {
            return getEntityService(entityType).update(id, data);
        }

        function createEntity(entityProperties) {
            return getEntityService(entityProperties.type).create(
                entityProperties
            );
        }

        function cloneEntity(entityType, id, data) {
            return getEntityService(entityType).clone(id, data);
        }

        function executeAction(action, entityType, id) {
            var service = getEntityService(entityType);
            var actionFn = service.getAction(
                constants.entityActionType.SINGLE,
                action
            );
            return actionFn(id);
        }

        function executeBulkAction(action, level, breakdown, id, selection) {
            var service = getEntityServiceByLevel(level, breakdown);
            var actionFn = service.getAction(
                constants.entityActionType.BULK,
                action,
                breakdown
            );
            return actionFn(id, selection);
        }

        function getEntityService(entityType) {
            if (entityType === constants.entityType.ACCOUNT)
                return zemAccountService;
            if (entityType === constants.entityType.CAMPAIGN)
                return zemCampaignService;
            if (entityType === constants.entityType.AD_GROUP)
                return zemAdGroupService;
            if (entityType === constants.entityType.CONTENT_AD)
                return zemContentAdService;
        }

        function getEntityServiceByLevel(level, breakdown) {
            if (
                breakdown === constants.breakdown.MEDIA_SOURCE ||
                breakdown === constants.breakdown.PUBLISHER
            ) {
                return getEntityService(constants.levelToEntityTypeMap[level]);
            }
            return getEntityService(getEntityTypeFromBreakdown(breakdown));
        }

        //
        // Helper map: breakdown -> entityType
        //
        function getEntityTypeFromBreakdown(breakdown) {
            if (breakdown === constants.breakdown.ACCOUNT)
                return constants.entityType.ACCOUNT;
            if (breakdown === constants.breakdown.CAMPAIGN)
                return constants.entityType.CAMPAIGN;
            if (breakdown === constants.breakdown.AD_GROUP)
                return constants.entityType.AD_GROUP;
            if (breakdown === constants.breakdown.CONTENT_AD)
                return constants.entityType.CONTENT_AD;
        }
    });
