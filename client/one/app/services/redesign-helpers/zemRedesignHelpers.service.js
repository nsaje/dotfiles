// TODO: Temporary service used to handle redesing related permission. Remove once redesign is finished.
angular.module('one.services').service('zemRedesignHelpersService', ['$window', 'zemPermissions', function ($window, zemPermissions) { // eslint-disable-line max-len
    this.setBodyThemeClass = setBodyThemeClass;

    function setBodyThemeClass () {
        var body = $('body');
        if (zemPermissions.hasPermission('zemauth.can_see_new_theme')) {
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
