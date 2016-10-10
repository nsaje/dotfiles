angular.module('one.widgets').service('zemHeaderMenuService', ['$window', '$uibModal', 'zemPermissions', 'zemFullStoryService', 'zemRedesignHelpersService', function ($window, $uibModal, zemPermissions, zemFullStoryService, zemRedesignHelpersService) { // eslint-disable-line max-len
    this.getAvailableActions = getAvailableActions;

    var ACTIONS = [
        {
            text: 'Demo mode',
            callback: navigate,
            params: {href: '/demo_mode'},
            isAvailable: zemPermissions.hasPermission('zemauth.switch_to_demo_mode'),
            isInternalFeature: zemPermissions.isPermissionInternal('zemauth.switch_to_demo_mode'),
        },
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
        {
            text: 'Toggle new layout',
            callback: zemRedesignHelpersService.toggleNewLayout,
            isAvailable: zemPermissions.hasPermission('zemauth.can_toggle_new_design'),
            isInternalFeature: zemPermissions.isPermissionInternal('zemauth.can_toggle_new_design'),
        },
        {
            text: 'Toggle new theme',
            callback: zemRedesignHelpersService.toggleNewTheme,
            isAvailable: zemPermissions.hasPermission('zemauth.can_toggle_new_design'),
            isInternalFeature: zemPermissions.isPermissionInternal('zemauth.can_toggle_new_design'),
        },
    ];

    function getAvailableActions () {
        return ACTIONS.filter(function (action) {
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

    function navigate (params) {
        $window.location.href = params.href;
    }

    function isAllowLivestreamActionAvailable () {
        return !zemFullStoryService.isLivestreamAllowed();
    }

    function requestDemoAction () {
        $uibModal.open({
            component: 'zemDemoRequest',
            windowClass: 'modal-default',
        });
    }
}]);
