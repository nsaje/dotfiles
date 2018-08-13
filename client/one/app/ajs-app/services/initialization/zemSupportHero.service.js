angular
    .module('one.services')
    .factory('zemSupportHeroService', function($window) {
        function boot(user) {
            if ($window.supportHeroWidget !== undefined) {
                var properties = {
                    custom: {
                        customerId: user.id,
                        userEmail: user.email,
                        userName: user.name,
                        language: 'en_US',
                    },
                };
                $window.supportHeroWidget.track(properties);
            }
        }
        return {
            boot: boot,
        };
    });
