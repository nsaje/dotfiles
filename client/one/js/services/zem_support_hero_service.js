/*globals SupprtHero*/
'use strict';

oneApp.factory('zemSupportHeroService', ['$window', function ($window) {
    function boot (user) {
        if ($window.supportHeroWidget != undefined) {
            var properties = {
                custom: {
                    customerId: user.id,
                    userEmail: user.email,
                    userName: user.name
                }
            };
            $window.supportHeroWidget.track(properties);
        }
    }
    return {
        boot: boot
    };
}]);
