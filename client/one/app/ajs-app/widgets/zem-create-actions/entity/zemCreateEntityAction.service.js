angular
    .module('one.widgets')
    .service('zemCreateEntityActionService', function(
        $q,
        $state,
        zemEntityService,
        zemNavigationService,
        zemNavigationNewService,
        zemUploadService
    ) {
        this.createEntity = createEntity;

        function createEntity(entityProperties) {
            if (entityProperties.type === constants.entityType.CONTENT_AD) {
                return createContentAds(entityProperties.parent);
            }

            return zemEntityService.createEntity(entityProperties).then(
                function(entity) {
                    entity.type = entityProperties.type;
                    reloadCache(entityProperties.parent, entity);
                    zemNavigationNewService.navigateTo(entity, {
                        settings: 'create',
                    });
                },
                function(err) {
                    return $q.reject(err);
                }
            );
        }

        function createContentAds(parent) {
            return zemUploadService.openUploadModal(parent, function onSave() {
                $state.reload();
            });
        }

        function reloadCache(parentEntity, entity) {
            // FIXME: Legacy workaround - When navigation service will be completely removed
            // this should be done automatically by listening entity services
            if (entity.type === constants.entityType.ACCOUNT) {
                zemNavigationService.reloadAccount(entity.id);
            }
            if (entity.type === constants.entityType.CAMPAIGN) {
                zemNavigationService.reloadCampaign(entity.id);
            }
            if (entity.type === constants.entityType.AD_GROUP) {
                zemNavigationService.reloadAdGroup(entity.id);
            }
        }
    });
