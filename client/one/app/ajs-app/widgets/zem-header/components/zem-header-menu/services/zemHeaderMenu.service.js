var commonHelpers = require('../../../../../../shared/helpers/common.helpers');
var RoutePathName = require('../../../../../../app.constants').RoutePathName;
var LevelParam = require('../../../../../../app.constants').LevelParam;

angular
    .module('one.widgets')
    .service('zemHeaderMenuService', function(
        $window,
        NgRouter,
        $uibModal,
        zemAuthStore,
        zemNavigationNewService
    ) {
        // eslint-disable-line max-len
        this.getAvailableActions = getAvailableActions;

        var USER_ACTIONS = [
            {
                text: 'Request demo',
                callback: requestDemoAction,
                isAvailable: zemAuthStore.hasPermission(
                    'zemauth.can_request_demo_v3'
                ),
                isInternalFeature: zemAuthStore.isPermissionInternal(
                    'zemauth.can_request_demo_v3'
                ),
            },
            {
                text: 'Sign out',
                callback: navigate,
                params: {href: '/signout'},
            },
        ];

        var ACCOUNT_ACTIONS = [
            {
                text: 'Pixels & Audiences',
                callback: navigateToPixelsView,
                isAvailable: isPixelsViewAvailable,
            },
            {
                text: 'Scheduled reports',
                callback: navigateToScheduledReportsView,
                isAvailable: true,
                isInternalFeature: false,
            },
        ];

        var MANAGEMENT_CONSOLE_ACTIONS = [
            {
                text: 'Credits',
                callback: navigateToCreditsView,
                isAvailable: isCreditsViewAvailable,
                isInternalFeature: zemAuthStore.isPermissionInternal(
                    'zemauth.account_credit_view'
                ),
            },
            {
                text: 'Deals',
                callback: navigateToDealsView,
                isAvailable: true,
            },
            {
                text: 'User management',
                callback: navigateToUsersView,
                isAvailable: true,
                isNewFeature: true,
            },
            {
                text: 'Publishers & placements',
                callback: navigateToPublisherGroupsView,
                isAvailable: true,
            },
            {
                text: 'Automation rules',
                callback: navigateToRulesView,
                isAvailable: isRulesViewAvailable,
                isInternalFeature: zemAuthStore.isPermissionInternal(
                    'zemauth.fea_can_create_automation_rules'
                ),
                isNewFeature: true,
            },
        ];

        var UTILITY_ACTIONS = [
            {
                text: 'Inventory planning',
                callback: navigateToInventoryPlanning,
            },
        ];

        function getAvailableActions(navigationGroup) {
            if (navigationGroup === 'user') {
                return USER_ACTIONS.filter(filterActions);
            } else if (navigationGroup === 'account') {
                return ACCOUNT_ACTIONS.filter(filterActions);
            } else if (navigationGroup === 'managementConsole') {
                return MANAGEMENT_CONSOLE_ACTIONS.filter(filterActions);
            } else if (navigationGroup === 'utility') {
                return UTILITY_ACTIONS.filter(filterActions);
            }
            return false;
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

        function navigate(params) {
            $window.location.href = params.href;
        }

        function navigateToPublisherGroupsView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();

            if (commonHelpers.isDefined(activeAccount)) {
                NgRouter.navigate(
                    [RoutePathName.APP_BASE, RoutePathName.PUBLISHER_GROUPS],
                    {
                        queryParams: {
                            agencyId: activeAccount.data.agencyId,
                            accountId: activeAccount.id,
                        },
                    }
                );
            } else {
                NgRouter.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.PUBLISHER_GROUPS,
                ]);
            }
        }

        function isCreditsViewAvailable() {
            return zemAuthStore.hasPermission('zemauth.account_credit_view');
        }

        function navigateToCreditsView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();

            if (commonHelpers.isDefined(activeAccount)) {
                NgRouter.navigate(
                    [RoutePathName.APP_BASE, RoutePathName.CREDITS],
                    {
                        queryParams: {
                            agencyId: activeAccount.data.agencyId,
                            accountId: activeAccount.id,
                        },
                    }
                );
            } else {
                NgRouter.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.CREDITS,
                ]);
            }
        }

        function navigateToScheduledReportsView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            if (activeAccount) {
                NgRouter.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.SCHEDULED_REPORTS,
                    LevelParam.ACCOUNT,
                    activeAccount.id,
                ]);
            } else if (activeAccount === null) {
                NgRouter.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.SCHEDULED_REPORTS,
                    LevelParam.ACCOUNTS,
                ]);
            }
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

        function navigateToPixelsView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            NgRouter.navigate([
                RoutePathName.APP_BASE,
                RoutePathName.PIXELS_LIBRARY,
                LevelParam.ACCOUNT,
                activeAccount.id,
            ]);
        }

        function navigateToDealsView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();

            if (commonHelpers.isDefined(activeAccount)) {
                NgRouter.navigate(
                    [RoutePathName.APP_BASE, RoutePathName.DEALS],
                    {
                        queryParams: {
                            agencyId: activeAccount.data.agencyId,
                            accountId: activeAccount.id,
                        },
                    }
                );
            } else {
                NgRouter.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.DEALS,
                ]);
            }
        }

        function navigateToUsersView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();

            if (commonHelpers.isDefined(activeAccount)) {
                NgRouter.navigate(
                    [RoutePathName.APP_BASE, RoutePathName.USERS],
                    {
                        queryParams: {
                            agencyId: activeAccount.data.agencyId,
                            accountId: activeAccount.id,
                        },
                    }
                );
            } else {
                NgRouter.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.USERS,
                ]);
            }
        }

        function isRulesViewAvailable() {
            return zemAuthStore.hasPermission(
                'zemauth.fea_can_create_automation_rules'
            );
        }

        function navigateToRulesView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();

            if (commonHelpers.isDefined(activeAccount)) {
                NgRouter.navigate(
                    [RoutePathName.APP_BASE, RoutePathName.RULES],
                    {
                        queryParams: {
                            agencyId: activeAccount.data.agencyId,
                            accountId: activeAccount.id,
                        },
                    }
                );
            } else {
                NgRouter.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.RULES,
                ]);
            }
        }

        function navigateToInventoryPlanning() {
            NgRouter.navigate([
                RoutePathName.APP_BASE,
                RoutePathName.INVENTORY_PLANNING,
            ]);
        }
    });
