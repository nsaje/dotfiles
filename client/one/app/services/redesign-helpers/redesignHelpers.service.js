// TODO: Temporary service used to handle redesing related permission. Remove once redesign is finished.
angular.module('one.services').service('redesignHelpersService', ['$window', 'userService', 'zemLocalStorageService', function ($window, userService, zemLocalStorageService) {
    this.canSeeNewLayout = canSeeNewLayout;
    this.canSeeNewTheme = canSeeNewTheme;
    this.toggleNewLayout = toggleNewLayout;
    this.toggleNewTheme = toggleNewTheme;
    this.setBodyThemeClass = setBodyThemeClass;

    function canSeeNewLayout () {
        return userService.hasPermission('zemauth.can_see_new_design') && zemLocalStorageService.get('newLayout');
    }

    function canSeeNewTheme () {
        return userService.hasPermission('zemauth.can_see_new_design') && zemLocalStorageService.get('newTheme');
    }

    function toggleNewLayout () {
        if (userService.hasPermission('zemauth.can_see_new_design')) {
            zemLocalStorageService.set('newLayout', !zemLocalStorageService.get('newLayout'));
        } else {
            zemLocalStorageService.set('newLayout', false);
        }
    }

    function toggleNewTheme () {
        if (userService.hasPermission('zemauth.can_see_new_design')) {
            zemLocalStorageService.set('newTheme', !zemLocalStorageService.get('newTheme'));
        } else {
            zemLocalStorageService.set('newTheme', false);
        }
        setBodyThemeClass();
    }

    function setBodyThemeClass () {
        var body = $('body');
        if (canSeeNewTheme()) {
            body.removeClass('legacy-theme');
        } else {
            body.addClass('legacy-theme');
        }
    }
}]);
