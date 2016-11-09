angular.module('one.widgets').service('zemHeaderMenuService', function ($window, $uibModal, zemPermissions, zemFullStoryService) { // eslint-disable-line max-len
    this.getAvailableActions = getAvailableActions;

    var ACTIONS = [
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
            backdrop: 'static',
            keyboard: false,
            windowClass: 'modal-default',
        });
    }
});
