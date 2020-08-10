var commonHelpers = require('../../../../../../shared/helpers/common.helpers');
var RoutePathName = require('../../../../../../app.constants').RoutePathName;
var LevelParam = require('../../../../../../app.constants').LevelParam;

angular
    .module('one.widgets')
    .service('zemHeaderMenuService', function(
        $window,
        NgRouter,
        $uibModal,
        zemPermissions,
        zemNavigationNewService
    ) {
        // eslint-disable-line max-len
        this.getAvailableActions = getAvailableActions;

        var canUserSeeNewPublisherGroupsView = zemPermissions.hasPermission(
            'zemauth.can_see_new_publisher_library'
        );

        var USER_ACTIONS = [
            {
                text: 'Request demo',
                callback: requestDemoAction,
                isAvailable: zemPermissions.hasPermission(
                    'zemauth.can_request_demo_v3'
                ),
                isInternalFeature: zemPermissions.isPermissionInternal(
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
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.can_see_new_pixels_view'
                ),
            },
            {
                text: 'Scheduled reports',
                callback: navigateToScheduledReportsView,
                isAvailable: zemPermissions.hasPermission(
                    'zemauth.can_see_new_scheduled_reports'
                ),
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.can_see_new_scheduled_reports'
                ),
            },
            {
                text: 'User permissions',
                callback: navigateToUserPermissionsView,
                isAvailable: isUserPermissionsViewAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.account_agency_access_permissions'
                ),
            },
        ];

        var MANAGEMENT_CONSOLE_ACTIONS = [
            {
                text: 'Credits',
                callback: navigateToCreditsView,
                isAvailable: isCreditsViewAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.account_credit_view'
                ),
            },
            {
                text: 'Deals',
                callback: navigateToDealsView,
                isAvailable: isDealsViewAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.can_see_deals_library'
                ),
            },
            {
                text: 'User management',
                callback: navigateToUsersView,
                isAvailable: isUsersViewAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.can_see_user_management'
                ),
            },
            {
                text: canUserSeeNewPublisherGroupsView
                    ? 'Publishers & placements'
                    : 'Publisher Groups',
                callback: navigateToPublisherGroupsView,
                isAvailable: isPublisherGroupsViewAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.can_see_publisher_groups_ui'
                ),
                isNewFeature: canUserSeeNewPublisherGroupsView,
            },
            {
                text: 'Automation rules',
                callback: navigateToRulesView,
                isAvailable: isRulesViewAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.fea_can_create_automation_rules'
                ),
            },
        ];

        var UTILITY_ACTIONS = [
            {
                text: 'Inventory planning',
                callback: navigateToInventoryPlanning,
                isAvailable: zemPermissions.hasPermission(
                    'zemauth.fea_can_see_inventory_planning'
                ),
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.fea_can_see_inventory_planning'
                ),
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

        function isPublisherGroupsViewAvailable() {
            return (
                zemPermissions.hasPermission(
                    'zemauth.can_see_publisher_groups_ui'
                ) &&
                zemPermissions.hasPermission(
                    'zemauth.can_edit_publisher_groups'
                )
            );
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
            return zemPermissions.hasPermission('zemauth.account_credit_view');
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

        function isUserPermissionsViewAvailable() {
            if (
                !zemPermissions.hasPermission(
                    'zemauth.account_agency_access_permissions'
                ) ||
                zemPermissions.hasPermission(
                    'zemauth.fea_use_entity_permission'
                )
            ) {
                return false;
            }
            return commonHelpers.isDefined(
                zemNavigationNewService.getActiveAccount()
            );
        }

        function navigateToUserPermissionsView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            NgRouter.navigate([
                RoutePathName.APP_BASE,
                RoutePathName.USER_PERMISSIONS,
                LevelParam.ACCOUNT,
                activeAccount.id,
            ]);
        }

        function isPixelsViewAvailable() {
            if (
                !zemPermissions.hasPermission('zemauth.can_see_new_pixels_view')
            )
                return false;
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

        function isDealsViewAvailable() {
            return zemPermissions.hasPermission(
                'zemauth.can_see_deals_library'
            );
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

        function isUsersViewAvailable() {
            return (
                zemPermissions.hasPermission(
                    'zemauth.can_see_user_management'
                ) &&
                zemPermissions.hasPermission(
                    'zemauth.fea_use_entity_permission'
                )
            );
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
            return zemPermissions.hasPermission(
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
