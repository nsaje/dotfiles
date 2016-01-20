/*globals angular,oneApp,constants,options,moment*/
'use strict';

oneApp.factory('zemDemoContentAdsService', ['$q', function ($q) {
    var contentAdDeltas = {},
        adGroupAds = {},
        adGroupBulkDeltas = {},
        adGroupExcludedContentAds = {},
        pub = {
            set: function (adGroupId, contentAdId, data) {
                if (!adGroupAds[adGroupId]) { adGroupAds[adGroupId] = []; }
                if (!contentAdDeltas[contentAdId]) { contentAdDeltas[contentAdId] = {}; }
                if (adGroupAds[adGroupId].indexOf(contentAdId) === -1) {
                    adGroupAds[adGroupId].push(contentAdId);
                }
                angular.forEach(data, function (v, k) {
                    contentAdDeltas[contentAdId][k] = v;
                });
            },
            setBulk: function (adGroupId, includeIds, excludeIds, all, data) {
                if (!adGroupExcludedContentAds[adGroupId]) {
                    adGroupExcludedContentAds[adGroupId] = {};
                }
                if (!adGroupBulkDeltas[adGroupId]) { adGroupBulkDeltas[adGroupId] = {}; }
                if (all) {
                    angular.forEach(data, function (v, k) {
                        adGroupExcludedContentAds[adGroupId][k] = excludeIds || [];
                    });

                    // First apply to all ad group ads
                    angular.forEach(data, function (v, k) { adGroupBulkDeltas[adGroupId][k] = v; });
                    // Then apply specific ad data
                    angular.forEach(adGroupAds[adGroupId] || [], function (contentAdId) {
                        if ((excludeIds || []).indexOf(contentAdId) === -1) {
                            pub.set(adGroupId, contentAdId, data);
                        }
                    });
                }
                angular.forEach(includeIds || [], function (contentAdId) {
                    pub.set(adGroupId, contentAdId, data);
                });
            },
            apply: function (adGroupId, contentAdId, data) {
                var excludes = adGroupExcludedContentAds[adGroupId] || {};
                angular.forEach(adGroupBulkDeltas[adGroupId] || {}, function (v, k) {
                    if ((excludes[k] || []).indexOf(contentAdId) === -1) {
                        data[k] = v;
                    }
                });
                // Information about specific ads has a higher priority and it can overwrite
                // bulk ad group deltas
                angular.forEach(contentAdDeltas[contentAdId] || {}, function (v, k) {
                    data[k] = v;
                });
                return data;
            }
        };
    return pub;
}]);
