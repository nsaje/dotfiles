var commonHelpers = require('../../../../../../shared/helpers/common.helpers');
var RoutePathName = require('../../../../../../app.constants').RoutePathName;
var LevelParam = require('../../../../../../app.constants').LevelParam;
var clone = require('clone');

angular
    .module('one.widgets')
    .service('zemHeaderMenuService', function(
        $window,
        NgRouter,
        $uibModal,
        zemAuthStore,
        zemNavigationNewService,
        zemDataFilterService
    ) {
        this.getMenuStructure = getMenuStructure;

        var MENU_STRUCTURE = [
            {
                name: 'Account settings',
                actions: [
                    {
                        name: 'Pixels & Audiences',
                        getUrlTree: getPixelsUrlTree,
                        isAvailable: isPixelsViewAvailable,
                    },
                    {
                        name: 'Scheduled reports',
                        getUrlTree: getScheduledReportsUrlTree,
                    },
                ],
            },
            {
                name: 'Management console',
                actions: [
                    {
                        name: 'Credits',
                        getUrlTree: getCreditsUrlTree,
                        isAvailable: isCreditsViewAvailable,
                        isInternalFeature: zemAuthStore.isPermissionInternal(
                            'zemauth.account_credit_view'
                        ),
                    },
                    {
                        name: 'Deals',
                        getUrlTree: getDealsUrlTree,
                    },
                    {
                        name: 'User management',
                        getUrlTree: getUsersUrlTree,
                        isNewFeature: true,
                    },
                    {
                        name: 'Publishers & placements',
                        getUrlTree: getPublisherGroupsUrlTree,
                    },
                    {
                        name: 'Automation rules',
                        getUrlTree: getRulesUrlTree,
                        isAvailable: isRulesViewAvailable,
                        isInternalFeature: zemAuthStore.isPermissionInternal(
                            'zemauth.fea_can_create_automation_rules'
                        ),
                        isNewFeature: true,
                    },
                    {
                        name: 'Creative library',
                        getUrlTree: getCreativeLibraryUrlTree,
                        isAvailable: isCreativeLibraryViewAvailable,
                        isNewFeature: true,
                    },
                ],
            },
            {
                name: 'Utilities',
                actions: [
                    {
                        name: 'Inventory planning',
                        getUrlTree: getInventoryPlanningUrlTree,
                    },
                ],
            },
            {
                name: 'User settings',
                actions: [
                    {
                        name: 'Request demo',
                        callback: requestDemoAction,
                        isAvailable: zemAuthStore.hasPermission(
                            'zemauth.can_request_demo_v3'
                        ),
                        isInternalFeature: zemAuthStore.isPermissionInternal(
                            'zemauth.can_request_demo_v3'
                        ),
                    },
                    {
                        name: 'Sign out',
                        callback: signOut,
                    },
                ],
            },
        ];

        function getMenuStructure() {
            return MENU_STRUCTURE.map(function(menuGroup) {
                return {
                    name: menuGroup.name,
                    actions: menuGroup.actions
                        .filter(filterActions)
                        .map(addActionUrl),
                };
            });
        }

        function addActionUrl(action) {
            if (commonHelpers.isDefined(action.getUrlTree)) {
                var urlTree = action.getUrlTree();

                var actionWithUrl = clone(action);

                actionWithUrl.callback = function() {
                    NgRouter.navigateByUrl(urlTree);
                };
                actionWithUrl.url = urlTree.toString();

                delete actionWithUrl.getUrlTree;

                return actionWithUrl;
            }
            return clone(action);
        }

        function filterActions(action) {
            if (action.isAvailable === undefined) {
                // Include action if no constraint is provided
                return true;
            }
            if (typeof action.isAvailable === 'boolean') {
                return action.isAvailable;
            }
            if (typeof action.isAvailable === 'function') {
                return action.isAvailable();
            }
            return false;
        }

        function signOut() {
            $window.location.href = '/signout';
        }

        function getPublisherGroupsUrlTree() {
            return getManagementConsoleItemUrlTree(
                RoutePathName.PUBLISHER_GROUPS
            );
        }

        function isCreditsViewAvailable() {
            return zemAuthStore.hasPermission('zemauth.account_credit_view');
        }

        function getCreditsUrlTree() {
            return getManagementConsoleItemUrlTree(RoutePathName.CREDITS);
        }

        function getScheduledReportsUrlTree() {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            if (activeAccount) {
                return NgRouter.createUrlTree([
                    RoutePathName.APP_BASE,
                    RoutePathName.SCHEDULED_REPORTS,
                    LevelParam.ACCOUNT,
                    activeAccount.id,
                ]);
            }

            return NgRouter.createUrlTree([
                RoutePathName.APP_BASE,
                RoutePathName.SCHEDULED_REPORTS,
                LevelParam.ACCOUNTS,
            ]);
        }

        function requestDemoAction() {
            $uibModal.open({
                component: 'zemDemoRequest',
                backdrop: 'static',
                keyboard: false,
                windowClass: 'modal-default',
            });
        }

        function isPixelsViewAvailable() {
            return commonHelpers.isDefined(
                zemNavigationNewService.getActiveAccount()
            );
        }

        function getPixelsUrlTree() {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            return NgRouter.createUrlTree([
                RoutePathName.APP_BASE,
                RoutePathName.PIXELS_LIBRARY,
                LevelParam.ACCOUNT,
                activeAccount.id,
            ]);
        }

        function getDealsUrlTree() {
            return getManagementConsoleItemUrlTree(RoutePathName.DEALS);
        }

        function getUsersUrlTree() {
            return getManagementConsoleItemUrlTree(RoutePathName.USERS);
        }

        function isRulesViewAvailable() {
            return zemAuthStore.hasPermission(
                'zemauth.fea_can_create_automation_rules'
            );
        }

        function getRulesUrlTree() {
            return getManagementConsoleItemUrlTree(RoutePathName.RULES);
        }

        function getInventoryPlanningUrlTree() {
            return NgRouter.createUrlTree([
                RoutePathName.APP_BASE,
                RoutePathName.INVENTORY_PLANNING,
            ]);
        }

        function isCreativeLibraryViewAvailable() {
            return zemAuthStore.hasPermission(
                'zemauth.can_see_creative_library'
            );
        }

        function getCreativeLibraryUrlTree() {
            return getManagementConsoleItemUrlTree(RoutePathName.CREATIVES);
        }

        function getManagementConsoleItemUrlTree(itemPath) {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            if (commonHelpers.isDefined(activeAccount)) {
                return NgRouter.createUrlTree(
                    [RoutePathName.APP_BASE, itemPath],
                    {
                        queryParams: {
                            agencyId: activeAccount.data.agencyId,
                            accountId: activeAccount.id,
                        },
                    }
                );
            }

            var filteredAgency = (zemDataFilterService.getFilteredAgencies() ||
                [])[0];
            if (commonHelpers.isDefined(filteredAgency)) {
                return NgRouter.createUrlTree(
                    [RoutePathName.APP_BASE, itemPath],
                    {
                        queryParams: {
                            agencyId: filteredAgency,
                        },
                    }
                );
            }

            return NgRouter.createUrlTree([RoutePathName.APP_BASE, itemPath]);
        }
    });
