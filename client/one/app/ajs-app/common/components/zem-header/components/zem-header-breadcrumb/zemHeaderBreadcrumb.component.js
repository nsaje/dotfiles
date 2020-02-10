angular.module('one.common').component('zemHeaderBreadcrumb', {
    template: require('./zemHeaderBreadcrumb.component.html'),
    controller: function(
        $rootScope,
        $state,
        $location,
        $document,
        $window,
        config,
        zemPermissions,
        zemNavigationNewService
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.config = config;

        var zemStateChangeHandler,
            locationChangeUpdateHandler,
            activeEntityUpdateHandler,
            hierarchyUpdateHandler;

        $ctrl.$onInit = function() {
            update();

            zemStateChangeHandler = $rootScope.$on(
                '$zemStateChangeSuccess',
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
            if (zemStateChangeHandler) zemStateChangeHandler();
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

            var administrationPage = getAdministrationPage();
            if (administrationPage && administrationPage.root) {
                breadcrumb.push(administrationPage);
                return breadcrumb;
            } else if (administrationPage) {
                breadcrumb.push(administrationPage);
            }

            var includeQueryParmas = true;
            var reuseNestedState =
                !administrationPage && !$state.includes('v2');
            while (entity) {
                breadcrumb.unshift({
                    name: entity.name,
                    typeName: getTypeName(entity.type),
                    href: zemNavigationNewService.getEntityHref(
                        entity,
                        includeQueryParmas,
                        reuseNestedState
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
        function getAdministrationPage() { // eslint-disable-line complexity
            if ($state.includes('**.users') || $state.includes('v2.users')) {
                return {
                    typeName: 'Account settings',
                    name: 'User permissions',
                    href: $location.absUrl(),
                };
            }
            if (
                $state.includes('**.credit_v2') ||
                $state.includes('v2.accountCredit')
            ) {
                return {
                    typeName: 'Account settings',
                    name: 'Account credit',
                    href: $location.absUrl(),
                };
            }
            if (
                $state.includes('**.scheduled_reports_v2') ||
                $state.includes('v2.reports')
            ) {
                return {
                    typeName: 'Account settings',
                    name: 'Scheduled reports',
                    href: $location.absUrl(),
                };
            }
            if ($state.includes('**.pixels') || $state.includes('v2.pixels')) {
                return {
                    typeName: 'Account settings',
                    name: 'Pixels & Audiences',
                    href: $location.absUrl(),
                };
            }
            if ($state.includes('v2.dealsLibrary')) {
                return {
                    typeName: 'Account settings',
                    name: 'Deals library',
                    href: $location.absUrl(),
                };
            }
            if (
                $state.includes('**.publisherGroups') ||
                $state.includes('v2.publisherGroups')
            ) {
                return {
                    typeName: 'Account settings',
                    name: 'Publisher groups',
                    href: $location.absUrl(),
                };
            }
            if ($state.includes('v2.inventoryPlanning')) {
                return {
                    typeName: 'Utilities',
                    name: 'Inventory planning',
                    href: $location.absUrl(),
                    root: true,
                };
            }
            if ($state.includes('v2.createEntity')) {
                return {
                    typeName: 'Entity management',
                    name: 'New entity',
                    href: $location.absUrl(),
                };
            }
            return null;
        }
    },
});
