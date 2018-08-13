angular
    .module('one.widgets')
    .service('zemInfoboxEndpoint', function(
        $q,
        $http,
        zemDataFilterService,
        zemUtils
    ) {
        this.getInfoboxData = getInfoboxData;

        function getInfoboxData(entity) {
            var entityId = entity ? entity.id : null;
            var entityType = entity ? entity.type : null;
            var url = constructGetInfoboxDataUrl(entityId, entityType);
            var dateRange = zemDataFilterService.getDateRange();

            var params = {
                start_date: dateRange.startDate.format(),
                end_date: dateRange.endDate.format(),
            };

            params = setGetInfoboxDataParams(entityType, params);

            var deferred = $q.defer();
            $http
                .get(url, {params: params})
                .then(function(data) {
                    deferred.resolve(
                        zemUtils.convertToCamelCase(data.data.data)
                    );
                })
                .catch(function(error) {
                    deferred.reject(error);
                });

            return deferred.promise;
        }

        function constructGetInfoboxDataUrl(entityId, entityType) {
            switch (entityType) {
                case constants.entityType.AD_GROUP:
                    return '/api/ad_groups/' + entityId + '/overview/';
                case constants.entityType.CAMPAIGN:
                    return '/api/campaigns/' + entityId + '/overview/';
                case constants.entityType.ACCOUNT:
                    return '/api/accounts/' + entityId + '/overview/';
                case null:
                    return '/api/accounts/overview/';
                default:
                    return '';
            }
        }

        function setGetInfoboxDataParams(entityType, params) {
            params = angular.copy(params);

            if (entityType === constants.entityType.AD_GROUP) {
                var filteredSources = zemDataFilterService.getFilteredSources();
                if (filteredSources.length > 0) {
                    params.filtered_sources = filteredSources.join(',');
                }
            }

            if (entityType === null) {
                var filteredAgencies = zemDataFilterService.getFilteredAgencies();
                if (filteredAgencies.length > 0) {
                    params.filtered_agencies = filteredAgencies.join(',');
                }

                var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
                if (filteredAccountTypes.length > 0) {
                    params.filtered_account_types = filteredAccountTypes.join(
                        ','
                    );
                }
            }

            return params;
        }
    });
