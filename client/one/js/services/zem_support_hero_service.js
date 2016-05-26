/*globals SupprtHero*/
'use strict';

oneApp.factory('zemSupportHeroService', ['$window', function ($window) {
    function boot (user) {
        console.log(user);

        if (window.supportHeroWidget != undefined) {
            console.log(window.supportHeroWidget);
            return;

            var properties = {
                custom: {
                    language: 'en_US',
                    customerId: 1234,
                    userEmail: 'john@doe.com',
                    userName: 'John Doe' // Add whatever properties you need here
                }
            };
            window.supportHeroWidget.track(properties);
        }
        else {
            console.log("SupportHero unavailable");
        }
    }

    return {
        boot: boot
    };
}]);
