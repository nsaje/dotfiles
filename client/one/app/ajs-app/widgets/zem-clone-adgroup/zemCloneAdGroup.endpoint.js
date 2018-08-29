var convertFromName = require('../../../shared/helpers/constants.helpers');

angular
    .module('one.widgets')
    .service('zemCloneAdGroupEndpoint', function($q, $http) {
        this.clone = clone;

        function clone(adGroupId, config) {
            var url = '/rest/internal/adgroups/clone/',
                params = {
                    adGroupId: adGroupId,
                    destinationCampaignId: config.destinationCampaignId,
                    destinationAdGroupName: config.destinationAdGroupName,
                    cloneAds: !!config.cloneAds,
                };

            var deferred = $q.defer();
            $http
                .post(url, params)
                .then(function(data) {
                    deferred.resolve(convertFromApi(data.data.data));
                })
                .catch(function(data) {
                    deferred.reject(convertErrorsFromApi(data));
                });

            return deferred.promise;
        }

        function convertFromApi(data) {
            var converted = angular.extend({}, data);
            converted.id = parseInt(data.id);
            converted.parentId = parseInt(data.campaignId);
            converted.campaignId = parseInt(data.campaignId);
            converted.state = convertFromName.convertFromName(
                data.state,
                constants.settingsState
            );
            converted.status = convertFromName.convertFromName(
                data.status,
                constants.adGroupRunningStatus
            );
            converted.active = convertFromName.convertFromName(
                data.active,
                constants.infoboxStatus
            );
            return converted;
        }

        function convertErrorsFromApi(data) {
            var errors = data.data.details;

            return {
                destinationCampaignId: errors.destinationCampaignId
                    ? errors.destinationCampaignId[0]
                    : null,
                destinationAdGroupName: errors.destinationAdGroupName
                    ? errors.destinationAdGroupName[0]
                    : null,
                cloneAds: errors.cloneAds ? errors.cloneAds[0] : null,
                message: data.status === 500 ? 'Something went wrong' : null,
            };
        }
    });
