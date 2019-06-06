angular
    .module('one.widgets')
    .service('zemContentInsightsEndpoint', function(
        $q,
        $http,
        zemDataFilterService,
        zemUtils
    ) {
        // eslint-disable-line max-len
        this.getData = getData;

        function getData(entity) {
            var deferred = $q.defer();
            var url = getUrl(entity);
            var config = {
                params: {},
            };

            var dateRange = zemDataFilterService.getDateRange();
            config.params.start_date = dateRange.startDate.format('YYYY-MM-DD');
            config.params.end_date = dateRange.endDate.format('YYYY-MM-DD');

            $http
                .get(url, config)
                .then(function(response) {
                    if (response.data && response.data.data) {
                        var data = response.data.data;
                        var convertedData = zemUtils.convertToCamelCase(data);
                        deferred.resolve(convertedData);
                    }
                })
                .catch(function(response) {
                    deferred.reject(response.data);
                });

            return deferred.promise;
        }

        function getUrl(entity) {
            if (entity.type === 'campaign') {
                return '/api/campaigns/' + entity.id + '/content-insights/';
            }

            throw '[ContentInsights Endpoint] Unsupported entity type';
        }
    });
