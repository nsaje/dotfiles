// TODO: Temporary service used to handle redesing related permission. Remove once redesign is finished.
angular.module('one.services').service('zemRedesignHelpersService', ['$window', 'zemUserService', 'zemLocalStorageService', function ($window, zemUserService, zemLocalStorageService) { // eslint-disable-line max-len
    this.userCanSeeNewLayout = userCanSeeNewLayout;
    this.userCanSeeNewTheme = userCanSeeNewTheme;
    this.toggleNewLayout = toggleNewLayout;
    this.toggleNewTheme = toggleNewTheme;
    this.setBodyThemeClass = setBodyThemeClass;

    function userCanSeeNewLayout () {
        return zemUserService.userHasPermissions('zemauth.can_toggle_new_design')
               && zemLocalStorageService.get('newLayout');
    }

    function userCanSeeNewTheme () {
        return zemUserService.userHasPermissions('zemauth.can_toggle_new_design')
               && zemLocalStorageService.get('newTheme');
    }

    function toggleNewLayout () {
        if (zemUserService.userHasPermissions('zemauth.can_toggle_new_design')) {
            zemLocalStorageService.set('newLayout', !zemLocalStorageService.get('newLayout'));
        } else {
            zemLocalStorageService.set('newLayout', false);
        }
    }

    function toggleNewTheme () {
        if (zemUserService.userHasPermissions('zemauth.can_toggle_new_design')) {
            zemLocalStorageService.set('newTheme', !zemLocalStorageService.get('newTheme'));
        } else {
            zemLocalStorageService.set('newTheme', false);
        }
        setBodyThemeClass();
    }

    function setBodyThemeClass () {
        var body = $('body');
        if (userCanSeeNewTheme()) {
            body.removeClass('legacy-theme');
        } else {
            body.addClass('legacy-theme');
        }
    }
}]);
