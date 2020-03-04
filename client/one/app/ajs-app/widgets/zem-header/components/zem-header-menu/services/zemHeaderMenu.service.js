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
                text: 'Account credit',
                callback: navigateToAccountCreditView,
                isAvailable: isAccountCreditActionAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.account_credit_view'
                ),
            },
            {
                text: 'Pixels & Audiences',
                callback: navigateToPixelsView,
                isAvailable: isPixelsViewAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.can_see_new_pixels_view'
                ),
            },
            {
                text: 'Publisher groups',
                callback: navigateToPublisherGroupsView,
                isAvailable: isPublisherGroupsActionAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.can_see_publisher_groups_ui'
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
                callback: navigateToUserPermissions,
                isAvailable: isUserPermissionsAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.account_agency_access_permissions'
                ),
            },
        ];

        var MANAGEMENT_CONSOLE_ACTIONS = [
            {
                text: 'Deals Library',
                callback: navigateToDealsLibraryView,
                isAvailable: isDealsLibraryViewAvailable,
                isInternalFeature: zemPermissions.isPermissionInternal(
                    'zemauth.can_see_deals_library'
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

        function isAccountCreditActionAvailable() {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            return (
                activeAccount &&
                zemPermissions.hasPermission(
                    'zemauth.can_see_new_account_credit'
                ) &&
                zemPermissions.hasPermission('zemauth.account_credit_view')
            );
        }

        function isPublisherGroupsActionAvailable() {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            return (
                activeAccount &&
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
            NgRouter.navigate([
                RoutePathName.APP_BASE,
                RoutePathName.PUBLISHER_GROUPS_LIBRARY,
                LevelParam.ACCOUNT,
                activeAccount.id,
            ]);
        }

        function navigateToAccountCreditView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            NgRouter.navigate([
                RoutePathName.APP_BASE,
                RoutePathName.CREDITS_LIBRARY,
                LevelParam.ACCOUNT,
                activeAccount.id,
            ]);
        }

        function navigateToScheduledReportsView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            if (activeAccount) {
                NgRouter.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.REPORTS_LIBRARY,
                    LevelParam.ACCOUNT,
                    activeAccount.id,
                ]);
            } else if (activeAccount === null) {
                NgRouter.navigate([
                    RoutePathName.APP_BASE,
                    RoutePathName.REPORTS_LIBRARY,
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

        function isUserPermissionsAvailable() {
            if (
                !zemPermissions.hasPermission(
                    'zemauth.account_agency_access_permissions'
                )
            )
                return false;
            return commonHelpers.isDefined(
                zemNavigationNewService.getActiveAccount()
            );
        }

        function navigateToUserPermissions() {
            var activeAccount = zemNavigationNewService.getActiveAccount();
            NgRouter.navigate([
                RoutePathName.APP_BASE,
                RoutePathName.USERS_LIBRARY,
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

        function isDealsLibraryViewAvailable() {
            return zemPermissions.hasPermission(
                'zemauth.can_see_deals_library'
            );
        }

        function navigateToDealsLibraryView() {
            var activeAccount = zemNavigationNewService.getActiveAccount();

            if (commonHelpers.isDefined(activeAccount)) {
                NgRouter.navigate(
                    [RoutePathName.APP_BASE, RoutePathName.DEALS_LIBRARY],
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
                    RoutePathName.DEALS_LIBRARY,
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
