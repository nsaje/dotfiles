var RoutePathName = require('../../../app.constants').RoutePathName;
var commonHelpers = require('../../../shared/helpers/common.helpers');
var routerHelpers = require('../../../shared/helpers/router.helpers');

angular
    .module('one.services')
    .service('zemNavigationNewService', function(
        $rootScope,
        $q,
        $location,
        $timeout,
        NgRouter,
        zemNavigationService
    ) {
        // eslint-disable-line max-len
        this.init = init;
        this.navigateTo = navigateTo;
        this.reloadCurrentRoute = reloadCurrentRoute;
        this.getEntityHref = getEntityHref;
        this.getHomeHref = getHomeHref;
        this.getEntityById = getEntityById;
        this.getActiveEntity = getActiveEntity;
        this.getActiveEntityByType = getActiveEntityByType;
        this.getActiveAccount = getActiveAccount;
        this.getNavigationHierarchy = getNavigationHierarchy;
        this.getNavigationHierarchyPromise = getNavigationHierarchyPromise;
        this.onHierarchyUpdate = onHierarchyUpdate;
        this.onHierarchyPartialUpdate = onHierarchyPartialUpdate;
        this.onActiveEntityChange = onActiveEntityChange;
        this.onBidModifierUpdate = onBidModifierUpdate;

        var EVENTS = {
            ON_HIERARCHY_UPDATE: 'zem-navigation-service-on-data-updated',
            ON_HIERARCHY_PARTIAL_UPDATE:
                'zem-navigation-service-on-data-partial-updated',
            ON_ACTIVE_ENTITY_CHANGE:
                'zem-navigation-service-on-active-entity-change',
            ON_BID_MODIFIER_UPDATE:
                'zem-navigation-service-on-bid-modifier-update',
        };

        var $scope = $rootScope.$new(); // Scope used for listener stuff (TODO: remove dependency)
        var hierarchyRoot; // Root of the navigation hierarchy tree (account -> campaign -> adgroup)
        var activeEntity; // Current navigation entity (e.g. ad group)

        function init() {
            handleNavigationChange();
            zemNavigationService.onUpdate($scope, handleDataUpdate);
            zemNavigationService.onBidModifierUpdate(
                $scope,
                handleBidModifierUpdate
            );

            $rootScope.$on('$zemNavigationEnd', handleNavigationChange);
        }

        function handleDataUpdate() {
            var accounts = zemNavigationService.getAccounts();
            buildHierarchyRootAsync(accounts);
        }

        function handleBidModifierUpdate() {
            notifyListeners(EVENTS.ON_BID_MODIFIER_UPDATE);
        }

        function handleNavigationChange() {
            var activatedRoute = routerHelpers.getActivatedRoute(NgRouter);
            var id = activatedRoute.snapshot.params.id;
            var level =
                constants.levelParamToLevelMap[
                    activatedRoute.snapshot.data.level
                ];
            var type = constants.levelToEntityTypeMap[level];

            if (
                NgRouter.url.includes(
                    RoutePathName.APP_BASE +
                        '/' +
                        RoutePathName.NEW_ENTITY_ANALYTICS_MOCK
                )
            ) {
                type = constants.entityToParentTypeMap[type];
            }

            getEntityById(type, id).then(setActiveEntity);
        }

        function buildHierarchyRootAsync(legacyAccounts) {
            var root = {};
            root.children = [];
            root.ids = {
                accounts: {},
                campaigns: {},
                adGroups: {},
            };

            var index = 0;
            (function doChunk() {
                var chunkSize = 100;
                while (chunkSize > 0 && index < legacyAccounts.length) {
                    var account = convertLegacyAccount(
                        root,
                        legacyAccounts[index]
                    );
                    root.children.push(account);
                    --chunkSize;
                    ++index;
                }
                if (index < legacyAccounts.length) {
                    $timeout(doChunk);
                    $timeout(
                        notifyListeners(
                            EVENTS.ON_HIERARCHY_PARTIAL_UPDATE,
                            root
                        )
                    );
                } else {
                    hierarchyRoot = root;
                    if (activeEntity) {
                        // Update entity with new object
                        getEntityById(activeEntity.type, activeEntity.id).then(
                            setActiveEntity
                        );
                    }
                    notifyListeners(EVENTS.ON_HIERARCHY_UPDATE, hierarchyRoot);
                }
            })();
        }

        function convertLegacyAccount(root, legacyAccount) {
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
            var urlTree = getUrlTree();
            var href = NgRouter.createUrlTree(urlTree).toString();
            if (
                NgRouter.url.includes(
                    RoutePathName.APP_BASE + '/' + RoutePathName.ANALYTICS
                )
            ) {
                var queryParams = $location.absUrl().split('?')[1];
                if (queryParams) href += '?' + queryParams;
            }
            return href;
        }

        // prettier-ignore
        function getUrlTree(entity) { // eslint-disable-line complexity
            var level = constants.levelParam.ACCOUNTS;
            var id = entity ? entity.id : null;

            var activatedRoute = routerHelpers.getActivatedRoute(NgRouter);
            var breakdown = activatedRoute.snapshot.params.breakdown;
            var isCampaign =
                entity && entity.type === constants.entityType.CAMPAIGN;
            if (
                (breakdown === constants.breakdownParam.INSIGHTS &&
                    !isCampaign)
            ) {
                breakdown = null;
            }

            if (entity && entity.type === constants.entityType.ACCOUNT)
                level = constants.levelParam.ACCOUNT;
            if (entity && entity.type === constants.entityType.CAMPAIGN)
                level = constants.levelParam.CAMPAIGN;
            if (entity && entity.type === constants.entityType.AD_GROUP)
                level = constants.levelParam.AD_GROUP;

            var urlTree = [RoutePathName.APP_BASE];

            if (entity && entity.data && entity.data.archived) {
                urlTree.push(RoutePathName.ARCHIVED);
            } else {
                urlTree.push(RoutePathName.ANALYTICS);
            }

            if (commonHelpers.isDefined(level)) {
                urlTree.push(level);
                if (commonHelpers.isDefined(id)) {
                    urlTree.push(id);
                }
            }
            if (commonHelpers.isDefined(breakdown)) {
                urlTree.push(breakdown);
            }

            return urlTree;
        }

        function getEntityHref(entity, includeQueryParams) {
            var urlTree = getUrlTree(entity);
            var href = NgRouter.createUrlTree(urlTree).toString();
            if (
                NgRouter.url.includes(
                    RoutePathName.APP_BASE + '/' + RoutePathName.ANALYTICS
                ) &&
                includeQueryParams
            ) {
                var queryParams = $location.absUrl().split('?')[1];
                if (queryParams) href += '?' + queryParams;
            }
            return href;
        }

        function navigateTo(entity) {
            var urlTree = getUrlTree(entity);
            var href = NgRouter.createUrlTree(urlTree).toString();
            if (
                NgRouter.url.includes(
                    RoutePathName.APP_BASE + '/' + RoutePathName.ANALYTICS
                )
            ) {
                var queryParams = $location.absUrl().split('?')[1];
                if (queryParams) href += '?' + queryParams;
            }
            return NgRouter.navigateByUrl(href);
        }

        function reloadCurrentRoute() {
            var url = NgRouter.url;
            NgRouter.navigate(['/'], {skipLocationChange: true}).then(
                function() {
                    NgRouter.navigateByUrl(url, {
                        queryParams: $location.search(),
                    });
                }
            );
        }

        function getEntityById(type, id) {
            if (!type) return $q.resolve(null);

            if (hierarchyRoot && zemNavigationService.isFullyLoaded()) {
                var entity = findEntityInHierarchyRoot(type, id);
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

            function findEntityInHierarchyRoot(type, id) {
                if (type === constants.entityType.ACCOUNT)
                    return hierarchyRoot.ids.accounts[id];
                if (type === constants.entityType.CAMPAIGN)
                    return hierarchyRoot.ids.campaigns[id];
                if (type === constants.entityType.AD_GROUP)
                    return hierarchyRoot.ids.adGroups[id];
            }

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
            if (
                commonHelpers.isDefined(activeEntity) &&
                commonHelpers.isDefined(entity) &&
                activeEntity.id === entity.id &&
                activeEntity.type === entity.type
            ) {
                return;
            }
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

        function onHierarchyPartialUpdate(callback) {
            return registerListener(
                EVENTS.ON_HIERARCHY_PARTIAL_UPDATE,
                callback
            );
        }

        function onActiveEntityChange(callback) {
            return registerListener(EVENTS.ON_ACTIVE_ENTITY_CHANGE, callback);
        }

        function onBidModifierUpdate(callback) {
            return registerListener(EVENTS.ON_BID_MODIFIER_UPDATE, callback);
        }

        function registerListener(event, callback) {
            return $scope.$on(event, callback);
        }

        function notifyListeners(event, data) {
            $scope.$emit(event, data);
        }
    });
