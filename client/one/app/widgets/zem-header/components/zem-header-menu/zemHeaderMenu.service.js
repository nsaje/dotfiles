angular.module('one.widgets').service('zemHeaderMenuService', ['$window', 'userService', 'redesignHelpersService', function ($window, userService, redesignHelpersService) {
    this.getAvailableActions = getAvailableActions;

    var ACTIONS = [
        {
            text: 'Demo mode',
            callback: navigate,
            params: {href: '/demo_mode'},
            isAvailable: userService.hasPermission('zemauth.switch_to_demo_mode'),
            isInternalFeature: userService.isPermissionInternal('zemauth.switch_to_demo_mode'),
        },
        {
            text: 'Request demo v3',
            callback: requestDemoAction,
            isAvailable: userService.hasPermission('zemauth.can_request_demo_v3'),
            isInternalFeature: userService.isPermissionInternal('zemauth.can_request_demo_v3'),
        },
        {
            text: 'Allow livestream',
            callback: allowLivestreamAction,
            isAvailable: isAllowLivestreamActionAvailable,
        },
        {
            text: 'Sing out',
            callback: navigate,
            params: {href: '/signout'},
        },
        {
            text: 'Toggle new layout',
            callback: redesignHelpersService.toggleNewLayout,
            isAvailable: userService.hasPermission('zemauth.can_see_new_design'),
        },
        {
            text: 'Toggle new theme',
            callback: redesignHelpersService.toggleNewTheme,
            isAvailable: userService.hasPermission('zemauth.can_see_new_design'),
        },
    ];
    var isLivestreamOn = false;

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

    function allowLivestreamAction () {
        isLivestreamOn = true;
        // TODO: Move this functionality to zemFullStoryService
    }

    function isAllowLivestreamActionAvailable () {
        return !isLivestreamOn;
    }

    function requestDemoAction () {
        // TODO
    }
}]);
