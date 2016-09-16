angular.module('one.widgets').service('zemHeaderMenuService', ['$window', '$uibModal', 'zemUserService', 'zemFullStoryService', 'zemRedesignHelpersService', function ($window, $uibModal, zemUserService, zemFullStoryService, zemRedesignHelpersService) { // eslint-disable-line max-len
    this.getAvailableActions = getAvailableActions;

    var ACTIONS = [
        {
            text: 'Demo mode',
            callback: navigate,
            params: {href: '/demo_mode'},
            isAvailable: zemUserService.userHasPermissions('zemauth.switch_to_demo_mode'),
            isInternalFeature: zemUserService.isPermissionInternal('zemauth.switch_to_demo_mode'),
        },
        {
            text: 'Request demo',
            callback: requestDemoAction,
            isAvailable: zemUserService.userHasPermissions('zemauth.can_request_demo_v3'),
            isInternalFeature: zemUserService.isPermissionInternal('zemauth.can_request_demo_v3'),
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
            isAvailable: zemUserService.userHasPermissions('zemauth.can_toggle_new_design'),
            isInternalFeature: zemUserService.isPermissionInternal('zemauth.can_toggle_new_design'),
        },
        {
            text: 'Toggle new theme',
            callback: zemRedesignHelpersService.toggleNewTheme,
            isAvailable: zemUserService.userHasPermissions('zemauth.can_toggle_new_design'),
            isInternalFeature: zemUserService.isPermissionInternal('zemauth.can_toggle_new_design'),
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
