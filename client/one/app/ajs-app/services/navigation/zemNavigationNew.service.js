angular
    .module('one.services')
    .service('zemNavigationNewService', function(
        $rootScope,
        $q,
        $location,
        $state,
        zemNavigationService,
        zemPermissions
    ) {
        // eslint-disable-line max-len
        this.init = init;
        this.navigateTo = navigateTo;
        this.refreshState = refreshState;
        this.getEntityHref = getEntityHref;
        this.getHomeHref = getHomeHref;
        this.getEntityById = getEntityById;
        this.getActiveEntity = getActiveEntity;
        this.getActiveEntityByType = getActiveEntityByType;
        this.getActiveAccount = getActiveAccount;
        this.getUsesBCMv2 = getUsesBCMv2;
        this.getNavigationHierarchy = getNavigationHierarchy;
        this.getNavigationHierarchyPromise = getNavigationHierarchyPromise;
        this.onHierarchyUpdate = onHierarchyUpdate;
        this.onActiveEntityChange = onActiveEntityChange;
        this.onUsesBCMv2Update = onUsesBCMv2Update;

        var EVENTS = {
            ON_HIERARCHY_UPDATE: 'zem-navigation-service-on-data-updated',
            ON_ACTIVE_ENTITY_CHANGE:
                'zem-navigation-service-on-active-entity-change',
            ON_USES_BCMV2_UPDATE: 'zem-navigation-service-on-uses-bcmv2-update',
        };

        var $scope = $rootScope.$new(); // Scope used for listener stuff (TODO: remove dependency)
        var hierarchyRoot; // Root of the navigation hierarchy tree (account -> campaign -> adgroup)
        var activeEntity; // Current navigation entity (e.g. ad group)
        var allAccountsUsesBCMv2 = false;

        function init() {
            zemNavigationService.onUpdate($scope, handleDataUpdate);

            initUsesBCMv2();

            $rootScope.$on('$zemStateChangeStart', function() {
                activeEntity = undefined;
            });
            $rootScope.$on('$zemStateChangeSuccess', handleStateChange);
        }

        function handleDataUpdate() {
            var legacyAccounts = zemNavigationService.getAccounts();
            hierarchyRoot = convertLegacyAccountsData(legacyAccounts);
            if (activeEntity) {
                // Update entity with new object
                getEntityById(activeEntity.type, activeEntity.id).then(
                    setActiveEntity
                );
            }
            notifyListeners(EVENTS.ON_HIERARCHY_UPDATE, hierarchyRoot);
        }

        function handleStateChange() {
            var id = $state.params.id;
            var level =
                constants.levelStateParamToLevelMap[$state.params.level];
            var type = constants.levelToEntityTypeMap[level];

            if ($state.includes('v2.createEntity')) {
                type = constants.entityToParentTypeMap[type];
            }

            getEntityById(type, id).then(setActiveEntity);
        }

        function initUsesBCMv2() {
            zemNavigationService.getUsesBCMv2().then(function(data) {
                allAccountsUsesBCMv2 = data.usesBCMv2;
                notifyListeners(EVENTS.ON_USES_BCMV2_UPDATE);
            });
        }

        function convertLegacyAccountsData(legacyAccounts) {
            var root = {};
            root.ids = {
                // Cache: id map (id -> entity)
                accounts: {},
                campaigns: {},
                adGroups: {},
            };
            // Convert legacy structure to new Entity hierarchy tree
            root.children = legacyAccounts.map(function(legacyAccount) {
                var account = createEntity(
                    constants.entityType.ACCOUNT,
                    null,
                    legacyAccount
                );
                root.ids.accounts[account.id] = account;
                account.children = legacyAccount.campaigns.map(function(
                    legacyCampaign
                ) {
                    var campaign = createEntity(
                        constants.entityType.CAMPAIGN,
                        account,
                        legacyCampaign
                    );
                    root.ids.campaigns[campaign.id] = campaign;
                    campaign.children = legacyCampaign.adGroups.map(function(
                        legacyAdGroup
                    ) {
                        var adGroup = createEntity(
                            constants.entityType.AD_GROUP,
                            campaign,
                            legacyAdGroup
                        );
                        root.ids.adGroups[adGroup.id] = adGroup;
                        return adGroup;
                    });
                    return campaign;
                });
                return account;
            });
            return root;
        }

        function createEntity(type, parent, data) {
            var entity = {};
            entity.id = data.id;
            entity.name = data.name;
            entity.parent = parent;
            entity.type = type;
            entity.data = data;
            return entity;
        }

        function getHomeHref() {
            var href;
            href = $state.href('v2.analytics', getTargetStateParams());

            var query = $location.absUrl().split('?')[1];
            if (query) href += '?' + query;

            return href;
        }

        // prettier-ignore
        function getTargetStateParams(entity) { // eslint-disable-line complexity
            var level = constants.levelStateParam.ACCOUNTS;
            var id = entity ? entity.id : null;

            var breakdown = $state.params.breakdown;
            var isAdGroup =
                entity && entity.type === constants.entityType.AD_GROUP;
            var isCampaign =
                entity && entity.type === constants.entityType.CAMPAIGN;
            if (
                (breakdown === constants.breakdownStateParam.PUBLISHERS &&
                    !isAdGroup &&
                    !zemPermissions.hasPermission(
                        'zemauth.can_see_publishers_all_levels'
                    )) ||
                (breakdown === constants.breakdownStateParam.INSIGHTS &&
                    !isCampaign)
            ) {
                breakdown = null;
            }

            if (entity && entity.type === constants.entityType.ACCOUNT)
                level = constants.levelStateParam.ACCOUNT;
            if (entity && entity.type === constants.entityType.CAMPAIGN)
                level = constants.levelStateParam.CAMPAIGN;
            if (entity && entity.type === constants.entityType.AD_GROUP)
                level = constants.levelStateParam.AD_GROUP;

            return {
                level: level,
                id: id,
                breakdown: breakdown,
            };
        }

        function getEntityHref(entity, includeQueryParams) {
            var href;
            href = $state.href('v2.analytics', getTargetStateParams(entity));

            if (includeQueryParams) {
                var query = $location.absUrl().split('?')[1];
                if (query) href += '?' + query;
            }
            return href;
        }

        function refreshState() {
            if ($state.includes('v2')) {
                $state.reload();
            } else {
                navigateTo(getActiveEntity());
            }
        }

        function navigateTo(entity, params) {
            if (!params) params = {};

            params = angular.extend(params, getTargetStateParams(entity));
            return $state.go('v2.analytics', params);
        }

        function redirectArchived(entity) {
            if (!entity) return;

            var level = constants.entityTypeToLevelMap[entity.type];
            var params = {
                level: constants.levelToLevelStateParamMap[level],
                id: entity.id,
            };

            if (
                entity.data &&
                entity.data.archived &&
                !$state.includes('v2.archived')
            ) {
                return $state.go('v2.archived', params);
            } else if (
                entity.data &&
                !entity.data.archived &&
                $state.includes('v2.archived')
            ) {
                return $state.go('v2.analytics', params);
            }
        }

        function getEntityById(type, id) {
            if (!type) return $q.resolve(null);

            if (hierarchyRoot) {
                var entity;
                if (type === constants.entityType.ACCOUNT)
                    entity = hierarchyRoot.ids.accounts[id];
                if (type === constants.entityType.CAMPAIGN)
                    entity = hierarchyRoot.ids.campaigns[id];
                if (type === constants.entityType.AD_GROUP)
                    entity = hierarchyRoot.ids.adGroups[id];

                if (entity) {
                    return $q.resolve(entity);
                }
            }

            if (type === constants.entityType.ACCOUNT)
                return zemNavigationService.getAccount(id).then(convertData);
            if (type === constants.entityType.CAMPAIGN)
                return zemNavigationService.getCampaign(id).then(convertData);
            if (type === constants.entityType.AD_GROUP)
                return zemNavigationService.getAdGroup(id).then(convertData);

            function convertData(data) {
                var entity;
                if (data && data.hasOwnProperty('account')) {
                    entity = createEntity(
                        constants.entityType.ACCOUNT,
                        null,
                        data.account
                    );
                }

                if (data && data.hasOwnProperty('campaign')) {
                    var campaign = createEntity(
                        constants.entityType.CAMPAIGN,
                        entity,
                        data.campaign
                    );
                    if (entity) entity.children = [campaign];
                    entity = campaign;
                }

                if (data && data.hasOwnProperty('adGroup')) {
                    var adGroup = createEntity(
                        constants.entityType.AD_GROUP,
                        entity,
                        data.adGroup
                    );
                    if (entity) entity.children = [adGroup];
                    entity = adGroup;
                }
                return entity;
            }
        }

        function setActiveEntity(entity) {
            if ($state.includes('v2') && redirectArchived(entity)) return;

            if (activeEntity === entity) return;
            activeEntity = entity;
            notifyListeners(EVENTS.ON_ACTIVE_ENTITY_CHANGE, activeEntity);
        }

        function getActiveEntity() {
            return activeEntity;
        }

        function getActiveAccount() {
            return getActiveEntityByType(constants.entityType.ACCOUNT);
        }

        function getActiveEntityByType(type) {
            var entity = activeEntity;
            while (entity) {
                if (entity.type === type) {
                    return entity;
                }
                entity = entity.parent;
            }
            return null;
        }

        function getUsesBCMv2() {
            var account = getActiveAccount();
            if (account) return account.data.usesBCMv2;

            return allAccountsUsesBCMv2;
        }

        function getNavigationHierarchy() {
            return hierarchyRoot;
        }

        function getNavigationHierarchyPromise() {
            if (hierarchyRoot) {
                return $q.resolve(getNavigationHierarchy());
            }

            var deferred = $q.defer();
            onHierarchyUpdate(function() {
                deferred.resolve(getNavigationHierarchy());
            });

            return deferred.promise;
        }

        //
        // Listener functionality (TODO: pubsub service)
        //
        function onHierarchyUpdate(callback) {
            return registerListener(EVENTS.ON_HIERARCHY_UPDATE, callback);
        }

        function onActiveEntityChange(callback) {
            return registerListener(EVENTS.ON_ACTIVE_ENTITY_CHANGE, callback);
        }

        function onUsesBCMv2Update(callback) {
            return registerListener(EVENTS.ON_USES_BCMV2_UPDATE, callback);
        }

        function registerListener(event, callback) {
            return $scope.$on(event, callback);
        }

        function notifyListeners(event, data) {
            $scope.$emit(event, data);
        }
    });
