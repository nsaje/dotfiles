angular.module('one.services').service('zemNavigationNewService', function ($rootScope, $location, $state, zemNavigationService) { // eslint-disable-line max-len
    this.init = init;
    this.navigateTo = navigateTo;
    this.refreshState = refreshState;
    this.getEntityHref = getEntityHref;
    this.getHomeHref = getHomeHref;
    this.getActiveEntity = getActiveEntity;
    this.getActiveEntityByType = getActiveEntityByType;
    this.getActiveAccount = getActiveAccount;
    this.getNavigationHierarchy = getNavigationHierarchy;
    this.onHierarchyUpdate = onHierarchyUpdate;
    this.onActiveEntityChange = onActiveEntityChange;

    var EVENTS = {
        ON_HIERARCHY_UPDATE: 'zem-navigation-service-on-data-updated',
        ON_ACTIVE_ENTITY_CHANGE: 'zem-navigation-service-on-active-entity-change',
    };

    var $scope = $rootScope.$new(); // Scope used for listener stuff (TODO: remove dependency)
    var hierarchyRoot; // Root of the navigation hierarchy tree (account -> campaign -> adgroup)
    var activeEntity; // Current navigation entity (e.g. ad group)

    function init () {
        zemNavigationService.onUpdate($scope, handleDataUpdate);
        $rootScope.$on('$zemStateChangeStart', function () {
            activeEntity = undefined;
        });
        $rootScope.$on('$zemStateChangeSuccess', handleStateChange);
    }

    function handleDataUpdate () {
        var legacyAccounts = zemNavigationService.getAccounts();
        hierarchyRoot = convertLegacyAccountsData(legacyAccounts);
        if (activeEntity) {
            // Update entity with new object
            activeEntity = getEntityById(activeEntity.type, activeEntity.id);
        }
        notifyListeners(EVENTS.ON_HIERARCHY_UPDATE, hierarchyRoot);
    }

    function handleStateChange () {
        var id = $state.params.id;
        var level = constants.levelStateParamToLevelMap[$state.params.level];
        var type = constants.levelToEntityTypeMap[level];

        if (hierarchyRoot) {
            var entity = getEntityById(type, id);
            setActiveEntity(entity);
        } else {
            // If hierarchy data not yet available use old workaround to get entity data
            fetchAndConvertLegacyEntityData(type, id);
        }
    }

    function fetchAndConvertLegacyEntityData (type, id) {
        if (type === null) return setActiveEntity(null); // On all accounts level
        if (type === constants.entityType.ACCOUNT) return zemNavigationService.getAccount(id).then(convertData);
        if (type === constants.entityType.CAMPAIGN) return zemNavigationService.getCampaign(id).then(convertData);
        if (type === constants.entityType.AD_GROUP) return zemNavigationService.getAdGroup(id).then(convertData);

        function convertData (data) {
            var entity;
            if (data && data.hasOwnProperty('account')) {
                entity = createEntity(constants.entityType.ACCOUNT, null, data.account);
            }

            if (data && data.hasOwnProperty('campaign')) {
                var campaign = createEntity(constants.entityType.CAMPAIGN, entity, data.campaign);
                if (entity) entity.children = [campaign];
                entity = campaign;
            }

            if (data && data.hasOwnProperty('adGroup')) {
                var adGroup = createEntity(constants.entityType.AD_GROUP, entity, data.adGroup);
                if (entity) entity.children = [adGroup];
                entity = adGroup;
            }
            setActiveEntity(entity);
        }
    }

    function convertLegacyAccountsData (legacyAccounts) {
        var root = {};
        root.ids = { // Cache: id map (id -> entity)
            accounts: {},
            campaigns: {},
            adGroups: {},
        };
        // Convert legacy structure to new Entity hierarchy tree
        root.children = legacyAccounts.map(function (legacyAccount) {
            var account = createEntity(constants.entityType.ACCOUNT, null, legacyAccount);
            root.ids.accounts[account.id] = account;
            account.children = legacyAccount.campaigns.map(function (legacyCampaign) {
                var campaign = createEntity(constants.entityType.CAMPAIGN, account, legacyCampaign);
                root.ids.campaigns[campaign.id] = campaign;
                campaign.children = legacyCampaign.adGroups.map(function (legacyAdGroup) {
                    var adGroup = createEntity(constants.entityType.AD_GROUP, campaign, legacyAdGroup);
                    root.ids.adGroups[adGroup.id] = adGroup;
                    return adGroup;
                });
                return campaign;
            });
            return account;
        });
        return root;
    }

    function createEntity (type, parent, data) {
        var entity = {};
        entity.id = data.id;
        entity.name = data.name;
        entity.parent = parent;
        entity.type = type;
        entity.data = data;
        return entity;
    }

    function getHomeHref () {
        var href;
        href = $state.href('v2.analytics', getTargetStateParams());

        var query = $location.absUrl().split('?')[1];
        if (query) href += '?' + query;

        return href;
    }

    function getTargetStateParams (entity) {
        var level = constants.levelStateParam.ACCOUNTS;
        var id = entity ? entity.id : null;

        var breakdown = $state.params.breakdown;
        var isAdGroup = entity && entity.type === constants.entityType.AD_GROUP;
        var isCampaign = entity && entity.type === constants.entityType.CAMPAIGN;
        if (breakdown === constants.breakdownStateParam.PUBLISHERS && !isAdGroup &&
            !zemPermissions.hasPermission('zemauth.can_see_publishers_all_levels') ||
            breakdown === constants.breakdownStateParam.INSIGHTS && !isCampaign
        ) {
            breakdown = null;
        }

        if (entity && entity.type === constants.entityType.ACCOUNT) level = constants.levelStateParam.ACCOUNT;
        if (entity && entity.type === constants.entityType.CAMPAIGN) level = constants.levelStateParam.CAMPAIGN;
        if (entity && entity.type === constants.entityType.AD_GROUP) level = constants.levelStateParam.AD_GROUP;

        return {
            level: level,
            id: id,
            breakdown: breakdown,
        };
    }

    function getEntityHref (entity, includeQueryParams) {
        var href;
        href = $state.href('v2.analytics', getTargetStateParams(entity));

        if (includeQueryParams) {
            var query = $location.absUrl().split('?')[1];
            if (query) href += '?' + query;
        }
        return href;
    }

    function refreshState () {
        if ($state.includes('v2')) {
            $state.reload();
        } else {
            navigateTo(getActiveEntity());
        }
    }

    function navigateTo (entity, params) {
        if (!params) params = {};

        params = angular.extend(params, getTargetStateParams(entity));
        return $state.go('v2.analytics', params);
    }

    function redirectArchived (entity) {
        if (!entity) return;

        var level = constants.entityTypeToLevelMap[entity.type];
        var params = {
            level: constants.levelToLevelStateParamMap[level],
            id: entity.id,
        };

        if (entity.data && entity.data.archived && !$state.includes('v2.archived')) {
            return $state.go('v2.archived', params);
        } else if (entity.data && !entity.data.archived && $state.includes('v2.archived')) {
            return $state.go('v2.analytics', params);
        }
    }

    function getEntityById (type, id) {
        if (!hierarchyRoot) return;
        if (type === constants.entityType.ACCOUNT) return hierarchyRoot.ids.accounts[id];
        if (type === constants.entityType.CAMPAIGN) return hierarchyRoot.ids.campaigns[id];
        if (type === constants.entityType.AD_GROUP) return hierarchyRoot.ids.adGroups[id];

        return null;
    }

    function setActiveEntity (entity) {
        if ($state.includes('v2') && redirectArchived(entity)) return;

        if (activeEntity === entity) return;
        activeEntity = entity;
        notifyListeners(EVENTS.ON_ACTIVE_ENTITY_CHANGE, activeEntity);
    }

    function getActiveEntity () {
        return activeEntity;
    }

    function getActiveAccount () {
        return getActiveEntityByType(constants.entityType.ACCOUNT);
    }

    function getActiveEntityByType (type) {
        var entity = activeEntity;
        while (entity) {
            if (entity.type === type) {
                return entity;
            }
            entity = entity.parent;
        }
        return null;
    }

    function getNavigationHierarchy () {
        return hierarchyRoot;
    }

    //
    // Listener functionality (TODO: pubsub service)
    //
    function onHierarchyUpdate (callback) {
        return registerListener(EVENTS.ON_HIERARCHY_UPDATE, callback);
    }

    function onActiveEntityChange (callback) {
        return registerListener(EVENTS.ON_ACTIVE_ENTITY_CHANGE, callback);
    }

    function registerListener (event, callback) {
        return $scope.$on(event, callback);
    }

    function notifyListeners (event, data) {
        $scope.$emit(event, data);
    }
});
