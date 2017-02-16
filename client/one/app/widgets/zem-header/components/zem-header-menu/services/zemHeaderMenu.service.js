angular.module('one.widgets').service('zemHeaderMenuService', function ($window, $state, $uibModal, zemPermissions, zemFullStoryService, zemNavigationNewService) { // eslint-disable-line max-len
    this.getAvailableActions = getAvailableActions;

    var USERACTIONS = [
        {
            text: 'Request demo',
            callback: requestDemoAction,
            isAvailable: zemPermissions.hasPermission('zemauth.can_request_demo_v3'),
            isInternalFeature: zemPermissions.isPermissionInternal('zemauth.can_request_demo_v3'),
        },
        {
            text: 'Allow livestream',
            callback: zemFullStoryService.allowLivestream,
            isAvailable: isAllowLivestreamActionAvailable,
        },
        {
            text: 'Sign out',
            callback: navigate,
            params: {href: '/signout'},
        },
    ];

    var ACCOUNTACTIONS = [
        {
            text: 'Reports',
            callback: navigateToScheduledReportsView,
            isAvailable: zemPermissions.hasPermission('zemauth.can_see_new_scheduled_reports'),
            isInternalFeature: zemPermissions.isPermissionInternal('zemauth.can_see_new_scheduled_reports'),
        },
        {
            text: 'User permissions',
            callback: navigateToUserPermissions,
            isAvailable: isUserPermissionsAvailable,
            isInternalFeature: zemPermissions.isPermissionInternal('zemauth.can_see_new_user_permissions'),
        },
    ];

    function getAvailableActions (navigationGroup) {
        if (navigationGroup === 'user') {
            return USERACTIONS.filter(function (action) {
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
            });
        } else if (navigationGroup === 'account') {
            return ACCOUNTACTIONS.filter(function (action) {
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
            });
        }

        return false;
    }

    function navigate (params) {
        $window.location.href = params.href;
    }

    function navigateToScheduledReportsView () {
        var activeAccount = zemNavigationNewService.getActiveAccount();
        if (activeAccount) {
            $state.go('main.accounts.scheduled_reports_v2', {id: activeAccount.id});
        } else if (activeAccount === null) {
            $state.go('main.allAccounts.scheduled_reports_v2');
        }
    }

    function isAllowLivestreamActionAvailable () {
        return !zemFullStoryService.isLivestreamAllowed();
    }

    function requestDemoAction () {
        $uibModal.open({
            component: 'zemDemoRequest',
            backdrop: 'static',
            keyboard: false,
            windowClass: 'modal-default',
        });
    }

    function isUserPermissionsAvailable () {
        if (!zemPermissions.hasPermission('zemauth.can_see_new_user_permissions')) return false;
        return zemNavigationNewService.getActiveAccount() !== null;
    }

    function navigateToUserPermissions () {
        var account = zemNavigationNewService.getActiveAccount();
        var state = 'main.accounts.users';
        var params = {id: account.id};
        $state.go(state, params);
    }
});
