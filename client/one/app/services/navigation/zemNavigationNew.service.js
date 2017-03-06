angular.module('one.services').service('zemNavigationNewService', function ($rootScope, $location, $state, zemNavigationService, zemPermissions) { // eslint-disable-line max-len
    this.init = init;
    this.navigateTo = navigateTo;
    this.refreshState = refreshState;
    this.getEntityHref = getEntityHref;
    this.getHomeHref = getHomeHref;
    this.getActiveEntity = getActiveEntity;
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
        $rootScope.$on('$stateChangeSuccess', handleStateChange);
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
        var type = null;

        if (zemPermissions.hasPermission('zemauth.can_use_new_routing') && $state.includes('v2.analytics')) {
            if ($state.params.level === 'account') type = constants.entityType.ACCOUNT;
            if ($state.params.level === 'campaign') type = constants.entityType.CAMPAIGN;
            if ($state.params.level === 'adgroup') type = constants.entityType.AD_GROUP;
        } else {
            if ($state.includes('main.accounts'))  type = constants.entityType.ACCOUNT;
            if ($state.includes('main.campaigns')) type = constants.entityType.CAMPAIGN;
            if ($state.includes('main.adGroups')) type = constants.entityType.AD_GROUP;
        }

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

    function getAccountEntityState (newState, $state) {
        if ($state.includes('**.credit')) newState += '.credit';
        // TODO: support permission checks here
        // if ($state.includes('**.budget')) state += '.credit';
        if ($state.includes('**.audiences')) newState += '.audiences';
        if ($state.includes('**.reports')) newState += '.reports';
        return newState;
    }

    function getCampaignEntityState (newState, $state) {
        if ($state.includes('**.credit')) newState += '.budget';
        if ($state.includes('**.budget')) newState += '.budget';
        return newState;
    }

    function getAdGroupEntityState (newState, $state) {
        if ($state.includes('**.publishers')) newState += '.publishers';
        return newState;
    }

    function getSpecialEntityState (entity, newState, $state) {
        if (entity.type === constants.entityType.ACCOUNT) {
            return getAccountEntityState(newState, $state);
        } else if (entity.type === constants.entityType.CAMPAIGN) {
            return getCampaignEntityState(newState, $state);
        } else if (entity.type === constants.entityType.AD_GROUP) {
            return getAdGroupEntityState(newState, $state);
        }
        return newState;
    }

    function getEntityState (entity) {
        var defaultState = getDefaultState(entity);
        var state = defaultState;

        // keep the same tab if possible
        // - standard
        if ($state.includes('**.sources')) state += '.sources';
        if ($state.includes('**.history')) state += '.history';
        if ($state.includes('**.settings')) state += '.settings';
        if ($state.includes('**.insights')) state += '.insights';
        // - special
        if (entity) state = getSpecialEntityState(entity, state, $state);

        if (!$state.get(state)) state = defaultState;

        return state;
    }

    function getDefaultState (entity) {
        var defaultState = 'main.allAccounts';
        if (entity) {
            switch (entity.type) {
            case constants.entityType.ACCOUNT:
                defaultState = 'main.accounts';
                break;
            case constants.entityType.CAMPAIGN:
                defaultState = 'main.campaigns';
                break;
            case constants.entityType.AD_GROUP:
                defaultState = 'main.adGroups';
                break;
            }
        }

        return defaultState;
    }

    function getHomeHref () {
        var href;
        if (zemPermissions.hasPermission('zemauth.can_use_new_routing')) {
            href = $state.href('v2.analytics', getTargetStateParams());
        } else {
            href = $state.href(getEntityState(), {});
        }

        var query = $location.absUrl().split('?')[1];
        if (query) href += '?' + query;

        return href;
    }

    function getTargetStateParams (entity) {
        var level = 'accounts';
        var id = entity ? entity.id : null;

        var breakdown = $state.params.breakdown;
        if (breakdown === 'publishers' && !(entity && entity.type === constants.entityType.AD_GROUP)) {
            breakdown = null;
        }

        if (entity && entity.type === constants.entityType.ACCOUNT) level = 'account';
        if (entity && entity.type === constants.entityType.CAMPAIGN) level = 'campaign';
        if (entity && entity.type === constants.entityType.AD_GROUP) level = 'adgroup';

        return {
            level: level,
            id: id,
            breakdown: breakdown,
        };
    }

    function getEntityHref (entity, includeQueryParams) {
        var href;
        if (zemPermissions.hasPermission('zemauth.can_use_new_routing')) {
            href = $state.href('v2.analytics', getTargetStateParams(entity));
        } else {
            href = $state.href(getEntityState(entity), {id: entity.id});
        }

        if (includeQueryParams) {
            var query = $location.absUrl().split('?')[1];
            if (query) href += '?' + query;
        }
        return href;
    }

    function refreshState () {
        navigateTo(getActiveEntity());
    }

    function navigateTo (entity) {
        if (zemPermissions.hasPermission('zemauth.can_use_new_routing')) {
            return $state.go('v2.analytics', getTargetStateParams(entity));
        }
        var state = getEntityState(entity);
        var params = entity ? {id: entity.id} : {};
        $state.go(state, params);
    }

    function getEntityById (type, id) {
        if (!hierarchyRoot) return null;
        if (type === constants.entityType.ACCOUNT) return hierarchyRoot.ids.accounts[id];
        if (type === constants.entityType.CAMPAIGN) return hierarchyRoot.ids.campaigns[id];
        if (type === constants.entityType.AD_GROUP) return hierarchyRoot.ids.adGroups[id];

        return null;
    }

    function setActiveEntity (entity) {
        if (activeEntity === entity) return;
        activeEntity = entity;
        notifyListeners(EVENTS.ON_ACTIVE_ENTITY_CHANGE, activeEntity);
    }

    function getActiveEntity () {
        return activeEntity;
    }

    function getActiveAccount () {
        var entity = activeEntity;
        while (entity) {
            if (entity.type === constants.entityType.ACCOUNT) {
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
