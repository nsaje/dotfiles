angular
    .module('one.widgets')
    .service('zemBidModifierApiService', function($http) {
        this.setBidModifier = setBidModifier;

        function createUrl(adGroupId) {
            return '/rest/v1/adgroups/' + adGroupId + '/publishers/';
        }

        function setBidModifier(
            adGroupId,
            sourceSlug,
            publisherDomain,
            blacklistStatus,
            modifier
        ) {
            var url = createUrl(adGroupId);

            if (modifier === 1.0) {
                modifier = null;
            }

            var data = {
                level: 'ADGROUP',
                source: sourceSlug,
                name: publisherDomain,
                modifier: modifier,
                status: blacklistStatus,
            };

            data = [data];
            return $http.put(url, data);
        }
    });
