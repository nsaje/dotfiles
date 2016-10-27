// TODO: Temporary service used to handle redesing related permission. Remove once redesign is finished.
angular.module('one.services').service('zemRedesignHelpersService', ['$window', 'zemPermissions', 'zemLocalStorageService', function ($window, zemPermissions, zemLocalStorageService) { // eslint-disable-line max-len
    this.userCanSeeNewLayout = userCanSeeNewLayout;
    this.userCanSeeNewTheme = userCanSeeNewTheme;
    this.toggleNewLayout = toggleNewLayout;
    this.toggleNewTheme = toggleNewTheme;
    this.setBodyThemeClass = setBodyThemeClass;

    function userCanSeeNewLayout () {
        return zemPermissions.hasPermission('zemauth.can_toggle_new_design')
               && zemLocalStorageService.get('newLayout');
    }

    function userCanSeeNewTheme () {
        return zemPermissions.hasPermission('zemauth.can_toggle_new_design')
               && zemLocalStorageService.get('newTheme');
    }

    function toggleNewLayout () {
        if (zemPermissions.hasPermission('zemauth.can_toggle_new_design')) {
            zemLocalStorageService.set('newLayout', !zemLocalStorageService.get('newLayout'));
        } else {
            zemLocalStorageService.set('newLayout', false);
        }
    }

    function toggleNewTheme () {
        if (zemPermissions.hasPermission('zemauth.can_toggle_new_design')) {
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

    // TEMPORARY SOLUTION SHOULD BE REFACTORED
    var lastScrollTop = 0;
    $(window).scroll(function () {
        var st = $(this).scrollTop();
        // FIXED HEADER
        if (st > 200) {
            $('body').addClass('fixed-header');
            $('body').removeClass('fade-fixed-header');
        } else if (st <= 200 && st > 100 && $('body').hasClass('fixed-header') && lastScrollTop > st) {
            $('body').addClass('fade-fixed-header');
        } else {
            $('body').removeClass('fixed-header');
        }
        lastScrollTop = st;
    });
}]);
