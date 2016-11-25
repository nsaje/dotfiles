// TODO: Temporary service used to handle redesing related permission. Remove once redesign is finished.
angular.module('one.services').service('zemRedesignHelpersService', function () {
    // TEMPORARY SOLUTION SHOULD BE REFACTORED
    $(window).scroll(function () {
        var st = $(this).scrollTop();
        // FIXED HEADER
        if (st > 50) {
            $('body').addClass('fixed-header');
        } else {
            $('body').removeClass('fixed-header');
        }
    });
});
