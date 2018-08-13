angular
    .module('one.services')
    .factory('zemGoogleAnalyticsService', function(
        $window,
        $location,
        $rootScope
    ) {
        var GA_KEY = 'UA-74379813-2';

        function init() {
            if (!$window.ga) return;

            $window.ga('create', GA_KEY, 'auto');
            $window.ga('send', 'pageview', $location.path());

            $rootScope.$on('$stateChangeSuccess', function() {
                $window.ga('send', 'pageview', $location.path());
            });
        }

        return {
            init: init,
        };
    });
