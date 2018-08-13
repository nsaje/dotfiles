angular
    .module('one.widgets')
    .factory('zemDemographicTargetingConstants', function() {
        // eslint-disable-line max-len

        var EXPRESSION_TYPE = {
            AND: 'and',
            OR: 'or',
            NOT: 'not',
            CATEGORY: 'category',
        };

        var PROVIDER = {
            BLUEKAI: 'bluekai',
        };

        return {
            EXPRESSION_TYPE: EXPRESSION_TYPE,
            PROVIDER: PROVIDER,
        };
    });
