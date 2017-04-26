/* global angular */

angular.module('one').config(function ($urlRouterProvider) {
    $urlRouterProvider.when('/signout', function ($location) {
        window.location = $location.absUrl();
    });

    $urlRouterProvider.otherwise('/');

    $urlRouterProvider.rule(function ($injector, $location) {
        var path = $location.url();

        // check to see if the path has a trailing slash
        if ('/' === path[path.length - 1]) {
            return path.replace(/\/$/, '');
        }

        if (path.indexOf('/?') > -1) {
            return path.replace('/?', '?');
        }

        return false;
    });

    // If new routing is used skip legacy redirects
    if (!window.zOne.useNewRouting) {
        $urlRouterProvider.when('/ad_groups/:adGroupId/ads_plus', '/ad_groups/:adGroupId/ads');

        $urlRouterProvider.when('/campaigns/:campaignId/budget', ['$state', '$match', function ($state, $match) {
            $state.go('main.campaigns.ad_groups', {
                id: $match.campaignId,
                settings: true,
                settingsScrollTo: 'zemCampaignBudgetsSettings'
            });
        }]);

        $urlRouterProvider.when('/:level/:id/history', ['$location', function ($location) {
            var url = $location.url().replace('/history', '?history');
            $location.url(url);
        }]);
    }
});
