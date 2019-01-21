angular
    .module('one.services')
    .service('zemCampaignService', function(
        $http,
        $q,
        zemEntityInstanceService,
        zemEntityActionsService
    ) {
        // eslint-disable-line max-len

        var entityInstanceService = zemEntityInstanceService.createInstance(
            constants.entityType.CAMPAIGN
        );
        var entityActionsService = zemEntityActionsService.createInstance(
            constants.entityType.CAMPAIGN
        );

        //
        // Public API
        //
        this.get = entityInstanceService.get;
        this.update = entityInstanceService.update;
        this.create = entityInstanceService.create;

        this.archive = entityActionsService.archive;
        this.restore = entityActionsService.restore;
        this.archiveCampaigns = entityActionsService.archiveEntities;
        this.restoreCampaigns = entityActionsService.restoreEntities;
        this.activateSources = entityActionsService.activateSources;
        this.deactivateSources = entityActionsService.deactivateSources;

        this.getAction = entityActionsService.getAction;
        this.onActionExecuted = entityActionsService.onActionExecuted;
        this.onEntityCreated = entityInstanceService.onEntityCreated; // TODO (jurebajt): Unused - remove
        this.onEntityUpdated = entityInstanceService.onEntityUpdated;
    });
