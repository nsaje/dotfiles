angular
    .module('one.services')
    .service('zemContentAdService', function(
        $http,
        $q,
        zemEntityActionsService
    ) {
        // eslint-disable-line max-len

        var entityActionsService = zemEntityActionsService.createInstance(
            constants.entityType.CONTENT_AD
        );

        this.archiveContentAds = entityActionsService.archiveEntities;
        this.restoreContentAds = entityActionsService.restoreEntities;
        this.activateContentAds = entityActionsService.activateEntities;
        this.deactivateContentAds = entityActionsService.deactivateEntities;
        this.editContentAds = entityActionsService.editEntities;
        this.cloneContentAds = entityActionsService.cloneEntities;

        this.getAction = entityActionsService.getAction;
        this.onActionExecuted = entityActionsService.onActionExecuted;
    });
