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
        // eslint-disable-line max-len

        this.createEntity = createEntity;

        function createEntity(entityType, parent) {
            if (entityType === constants.entityType.CONTENT_AD) {
                return createContentAds(parent);
            }

            var parentId = parent ? parent.id : undefined;
            return zemEntityService.createEntity(entityType, parentId).then(
                function(entity) {
                    entity.type = entityType;
                    reloadCache(parent, entity);
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
                zemNavigationService.addAccountToCache({
                    name: entity.name,
                    id: entity.id,
                    campaigns: [],
                });
            }
            if (entity.type === constants.entityType.CAMPAIGN) {
                zemNavigationService.addCampaignToCache(parentEntity.id, {
                    id: entity.id,
                    name: entity.name,
                    adGroups: [],
                });
            }
            if (entity.type === constants.entityType.AD_GROUP) {
                zemNavigationService.addAdGroupToCache(parentEntity.id, {
                    id: entity.id,
                    name: entity.name,
                    status: constants.settingsState.INACTIVE,
                    state: constants.adGroupRunningStatus.INACTIVE,
                });
            }
        }
    });
