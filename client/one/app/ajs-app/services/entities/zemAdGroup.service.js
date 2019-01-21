angular
    .module('one.services')
    .service('zemAdGroupService', function(
        $http,
        $q,
        zemEntityInstanceService,
        zemEntityActionsService
    ) {
        // eslint-disable-line max-len

        var entityInstanceService = zemEntityInstanceService.createInstance(
            constants.entityType.AD_GROUP
        );
        var entityActionsService = zemEntityActionsService.createInstance(
            constants.entityType.AD_GROUP
        );

        //
        // Public API
        //
        this.get = entityInstanceService.get;
        this.update = entityInstanceService.update;
        this.create = entityInstanceService.create;
        this.clone = entityInstanceService.clone;
        this.archive = entityActionsService.archive;
        this.restore = entityActionsService.restore;
        this.activate = entityActionsService.activate;
        this.deactivate = entityActionsService.deactivate;

        this.archiveAdGroups = entityActionsService.archiveEntities;
        this.restoreAdGroups = entityActionsService.restoreEntities;
        this.activateAdGroups = entityActionsService.activateEntities;
        this.deactivateAdGroups = entityActionsService.deactivateEntities;
        this.activateSources = entityActionsService.activateSources;
        this.deactivateSources = entityActionsService.deactivateSources;

        this.getAction = entityActionsService.getAction;
        this.onActionExecuted = entityActionsService.onActionExecuted;
        this.onEntityCreated = entityInstanceService.onEntityCreated; // TODO (jurebajt): Unused - remove
        this.onEntityUpdated = entityInstanceService.onEntityUpdated;
    });
