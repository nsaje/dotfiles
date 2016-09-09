angular.module('one.services').service('zemNavigationNewService', ['$rootScope', '$state', 'zemNavigationService', function ($rootScope, $state, zemNavigationService) {
    var EVENTS = {
        ON_HIERARCHY_UPDATE: 'zem-navigation-service-on-data-updated',
        ON_ACTIVE_ENTITY_CHANGE: 'zem-navigation-service-on-active-entity-change',
    };

    var $scope = $rootScope.$new(); // Scope used for listener stuff (TODO: remove dependency)
    var hierarchyRoot; // Root of the navigation hierarchy tree (account -> campaign -> adgroup)
    var activeEntity; // Current navigation entity (e.g. ad group)

    // Public API
    this.initialize = initialize;
    this.navigateTo = navigateTo;
    this.getActiveEntity = getActiveEntity;
    this.getActiveAccount = getActiveAccount;
    this.getNavigationHierarchy = getNavigationHierarchy;
    this.onHierarchyUpdate = onHierarchyUpdate;
    this.onActiveEntityChange = onActiveEntityChange;

    function initialize () {
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
        if ($state.includes('main.accounts'))  type = constants.entityType.ACCOUNT;
        if ($state.includes('main.campaigns')) type = constants.entityType.CAMPAIGN;
        if ($state.includes('main.adGroups')) type = constants.entityType.AD_GROUP;

        if (hierarchyRoot) {
            var entity = getEntityById(type, id);
            setActiveEntity(entity);
        } else {
            // If hierarchy data not yet available use old workaround to get entity data
            fetchAndConvertLegacyEntityData(type, id);
        }
    }

    function fetchAndConvertLegacyEntityData (type, id) {
        if (type === constants.entityType.ACCOUNT) zemNavigationService.getAccount(id).then(convertData);
        if (type === constants.entityType.CAMPAIGN) zemNavigationService.getCampaign(id).then(convertData);
        if (type === constants.entityType.AD_GROUP) zemNavigationService.getAdGroup(id).then(convertData);

        function convertData (data) {
            var entity;
            if (data.hasOwnProperty('account')) {
                entity = createEntity(constants.entityType.ACCOUNT, null, data.account);
            }

            if (data.hasOwnProperty('campaign')) {
                var campaign = createEntity(constants.entityType.CAMPAIGN, entity, data.campaign);
                if (entity) entity.children = [campaign];
                entity = campaign;
            }

            if (data.hasOwnProperty('adGroup')) {
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


    function navigateTo (entity) {
        var defaultState = 'main.allAccounts';
        var params = {};

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
            params = {id: entity.id};
        }

        // keep the same tab if possible
        var state = defaultState;
        if ($state.includes('**.sources')) state += '.sources';
        if ($state.includes('**.history')) state += '.history';
        if ($state.includes('**.settings')) state += '.settings';
        if (!$state.get(state)) state = defaultState;

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
}]);
