var RoutePathName = require('../../../../../app.constants').RoutePathName;
var ENTITY_TYPE_TO_LEVEL_MAP = require('../../../../../app.constants')
    .ENTITY_TYPE_TO_LEVEL_MAP;
var LEVEL_TO_LEVEL_PARAM_MAP = require('../../../../../app.constants')
    .LEVEL_TO_LEVEL_PARAM_MAP;

angular.module('one.widgets').component('zemHeaderBreadcrumb', {
    template: require('./zemHeaderBreadcrumb.component.html'),
    controller: function(
        $rootScope,
        NgRouter,
        $document,
        $window,
        config,
        zemPermissions,
        zemNavigationNewService,
        zemUtils
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.openUrl = openUrl;

        var zemNavigationEndHandler,
            locationChangeUpdateHandler,
            activeEntityUpdateHandler,
            hierarchyUpdateHandler;

        $ctrl.$onInit = function() {
            update();
            zemNavigationEndHandler = $rootScope.$on(
                '$zemNavigationEnd',
                update
            );
            locationChangeUpdateHandler = $rootScope.$on(
                '$locationChangeSuccess',
                update
            );
            activeEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(
                update
            );
            // FIXME: Use Entity services for name changes
            hierarchyUpdateHandler = zemNavigationNewService.onHierarchyUpdate(
                update
            );
        };

        $ctrl.$onDestroy = function() {
            if (zemNavigationEndHandler) zemNavigationEndHandler();
            if (locationChangeUpdateHandler) locationChangeUpdateHandler();
            if (activeEntityUpdateHandler) activeEntityUpdateHandler();
            if (hierarchyUpdateHandler) hierarchyUpdateHandler();
        };

        function update() {
            var activeEntity = zemNavigationNewService.getActiveEntity();
            $ctrl.breadcrumb = getBreadcrumb(activeEntity);
            updateTitle($ctrl.breadcrumb, activeEntity);
        }

        function updateTitle(breadcrumb, activeEntity) {
            var dashboardTitle =
                ($window.zOne.whitelabel &&
                    $window.zOne.whitelabel.dashboardTitle) ||
                'Zemanta';
            var title = '';
            if (activeEntity) {
                title = activeEntity.name + ' | ' + dashboardTitle;
            } else {
                title = breadcrumb[0] ? breadcrumb[0].name + ' | ' : '';
                title += dashboardTitle;
            }
            $document.prop('title', title);
        }

        function getBreadcrumb(entity) {
            var breadcrumb = [];

            var administrationPage = getAdministrationPage(entity);
            if (administrationPage) {
                breadcrumb.push(administrationPage);
                if (administrationPage.root) {
                    return breadcrumb;
                }
            }

            var includeQueryParams = true;
            while (entity) {
                breadcrumb.unshift({
                    name: entity.name,
                    typeName: getTypeName(entity.type),
                    href: zemNavigationNewService.getEntityHref(
                        entity,
                        includeQueryParams
                    ),
                });
                entity = entity.parent;
            }

            var canUserSeeAllAccounts = zemPermissions.hasPermission(
                'zemauth.can_see_all_accounts'
            );
            var name = canUserSeeAllAccounts ? 'All accounts' : 'My accounts';
            breadcrumb.unshift({
                name: name,
                typeName: 'Home',
                href: zemNavigationNewService.getHomeHref(),
            });

            return breadcrumb;
        }

        function getTypeName(type) {
            if (type === constants.entityType.ACCOUNT) return 'Account';
            if (type === constants.entityType.CAMPAIGN) return 'Campaign';
            if (type === constants.entityType.AD_GROUP) return 'Ad Group';
        }

        // prettier-ignore
        function getAdministrationPage(entity) { // eslint-disable-line complexity
            var entityId = entity ? entity.id : null;
            var levelParam = entity
                ? LEVEL_TO_LEVEL_PARAM_MAP[
                      ENTITY_TYPE_TO_LEVEL_MAP[entity.type]
                  ]
                : null;
            var queryParams = NgRouter.browserUrlTree.queryParams;
            var urlTree = [];
            if (NgRouter.url.includes(RoutePathName.APP_BASE + '/' + RoutePathName.USERS_LIBRARY)) {
                urlTree = [
                    RoutePathName.APP_BASE,
                    RoutePathName.USERS_LIBRARY
                ];
                if (levelParam) {
                    urlTree.push(levelParam);
                }
                if (entityId) {
                    urlTree.push(entityId);
                }
                return {
                    typeName: 'Account settings',
                    name: 'User permissions',
                    href: NgRouter.createUrlTree(urlTree, {queryParams: queryParams}).toString(),
                };
            } else if (NgRouter.url.includes(RoutePathName.APP_BASE + '/' + RoutePathName.CREDITS_LIBRARY)) {
                urlTree = [
                    RoutePathName.APP_BASE,
                    RoutePathName.CREDITS_LIBRARY
                ];
                return {
                    typeName: 'Management Console',
                    name: 'Credits Library',
                    href: NgRouter.createUrlTree(urlTree, {queryParams: queryParams}).toString(),
                };
            } else if (NgRouter.url.includes(RoutePathName.APP_BASE + '/' + RoutePathName.REPORTS_LIBRARY)) {
                urlTree = [
                    RoutePathName.APP_BASE,
                    RoutePathName.REPORTS_LIBRARY
                ];
                if (levelParam) {
                    urlTree.push(levelParam);
                }
                if (entityId) {
                    urlTree.push(entityId);
                }
                return {
                    typeName: 'Account settings',
                    name: 'Scheduled reports',
                    href: NgRouter.createUrlTree(urlTree, {queryParams: queryParams}).toString(),
                };
            } else if (NgRouter.url.includes(RoutePathName.APP_BASE + '/' + RoutePathName.PIXELS_LIBRARY)) {
                urlTree = [
                    RoutePathName.APP_BASE,
                    RoutePathName.PIXELS_LIBRARY
                ];
                if (levelParam) {
                    urlTree.push(levelParam);
                }
                if (entityId) {
                    urlTree.push(entityId);
                }
                return {
                    typeName: 'Account settings',
                    name: 'Pixels & Audiences',
                    href: NgRouter.createUrlTree(urlTree, {queryParams: queryParams}).toString(),
                };
            } else if (NgRouter.url.includes(RoutePathName.APP_BASE + '/' + RoutePathName.DEALS_LIBRARY)) {
                urlTree = [
                    RoutePathName.APP_BASE,
                    RoutePathName.DEALS_LIBRARY
                ];
                return {
                    typeName: 'Management Console',
                    name: 'Deals Library',
                    href: NgRouter.createUrlTree(urlTree, {queryParams: queryParams}).toString(),
                };
            } else if (NgRouter.url.includes(RoutePathName.APP_BASE + '/' + RoutePathName.PUBLISHER_GROUPS_LIBRARY)) {
                urlTree = [
                    RoutePathName.APP_BASE,
                    RoutePathName.PUBLISHER_GROUPS_LIBRARY
                ];
                if (levelParam) {
                    urlTree.push(levelParam);
                }
                if (entityId) {
                    urlTree.push(entityId);
                }
                return {
                    typeName: 'Account settings',
                    name: 'Publishers & Placements',
                    href: NgRouter.createUrlTree(urlTree, {queryParams: queryParams}).toString(),
                };
            } else if (NgRouter.url.includes(RoutePathName.APP_BASE + '/' + RoutePathName.INVENTORY_PLANNING)) {
                urlTree = [
                    RoutePathName.APP_BASE,
                    RoutePathName.INVENTORY_PLANNING
                ];
                return {
                    typeName: 'Utilities',
                    name: 'Inventory planning',
                    href: NgRouter.createUrlTree(urlTree).toString(),
                    root: true,
                };
            } else if (NgRouter.url.includes(RoutePathName.APP_BASE + '/' + RoutePathName.NEW_ENTITY_ANALYTICS_MOCK)) {
                urlTree = [
                    RoutePathName.APP_BASE,
                    RoutePathName.NEW_ENTITY_ANALYTICS_MOCK
                ];
                if (levelParam) {
                    urlTree.push(levelParam);
                }
                if (entityId) {
                    urlTree.push(entityId);
                }
                return {
                    typeName: 'Entity management',
                    name: 'New entity',
                    href: NgRouter.createUrlTree(urlTree).toString(),
                };
            }
            return null;
        }

        function openUrl($event, href) {
            $event.preventDefault();
            if (zemUtils.shouldOpenInNewTab($event)) {
                $window.open(href, '_blank');
            } else {
                NgRouter.navigateByUrl(href);
            }
        }
    },
});
