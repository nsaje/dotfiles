angular.module('one.widgets').service('zemHeaderMenuService', function ($window, $state, $uibModal, zemPermissions, zemFullStoryService, zemNavigationNewService) { // eslint-disable-line max-len
    this.getAvailableActions = getAvailableActions;

    var USER_ACTIONS = [
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

    var ACCOUNT_ACTIONS = [
        {
            text: 'Account credit',
            callback: navigateToAccountCreditView,
            isAvailable: isAccountCreditActionAvailable,
            isInternalFeature: zemPermissions.isPermissionInternal('zemauth.account_credit_view'),
        },
        {
            text: 'Pixels & Audiences',
            callback: navigateToPixelsView,
            isAvailable: isPixelsViewAvailable,
            isInternalFeature: zemPermissions.isPermissionInternal('zemauth.can_see_new_pixels_view'),
        },
        {
            text: 'Publisher groups',
            callback: navigateToPublisherGroupsView,
            isAvailable: isPublisherGroupsActionAvailable,
            isInternalFeature: zemPermissions.isPermissionInternal('zemauth.can_see_publisher_groups_ui'),
        },
        {
            text: 'Scheduled reports',
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
            return USER_ACTIONS.filter(filterActions);
        } else if (navigationGroup === 'account') {
            return ACCOUNT_ACTIONS.filter(filterActions);
        }
        return false;
    }

    function filterActions (action) {
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

    function navigate (params) {
        $window.location.href = params.href;
    }

    function isAccountCreditActionAvailable () {
        var activeAccount = zemNavigationNewService.getActiveAccount();
        return activeAccount &&
               zemPermissions.hasPermission('zemauth.can_see_new_account_credit') &&
               zemPermissions.hasPermission('zemauth.account_credit_view');
    }

    function isPublisherGroupsActionAvailable () {
        var activeAccount = zemNavigationNewService.getActiveAccount();
        return activeAccount &&
            zemPermissions.hasPermission('zemauth.can_see_publisher_groups_ui') &&
            zemPermissions.hasPermission('zemauth.can_edit_publisher_groups');
    }

    function navigateToPublisherGroupsView () {
        var activeAccount = zemNavigationNewService.getActiveAccount();
        $state.go('v2.publisherGroups', {id: activeAccount.id});
    }

    function navigateToAccountCreditView () {
        var activeAccount = zemNavigationNewService.getActiveAccount();
        $state.go('v2.accountCredit', {id: activeAccount.id});
    }

    function navigateToScheduledReportsView () {
        var activeAccount = zemNavigationNewService.getActiveAccount();
        if (activeAccount) {
            $state.go('v2.reports', {level: constants.levelStateParam.ACCOUNT, id: activeAccount.id});
        } else if (activeAccount === null) {
            $state.go('v2.reports', {level: constants.levelStateParam.ACCOUNTS});
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
        var activeAccount = zemNavigationNewService.getActiveAccount();
        $state.go('v2.users', {id: activeAccount.id});
    }

    function isPixelsViewAvailable () {
        if (!zemPermissions.hasPermission('zemauth.can_see_new_pixels_view')) return false;
        return zemNavigationNewService.getActiveAccount() !== null;
    }

    function navigateToPixelsView () {
        var activeAccount = zemNavigationNewService.getActiveAccount();
        $state.go('v2.pixels', {id: activeAccount.id});
    }
});
