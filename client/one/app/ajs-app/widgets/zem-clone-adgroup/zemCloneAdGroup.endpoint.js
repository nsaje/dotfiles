var constantsHelpers = require('../../../shared/helpers/constants.helpers');
var commonHelpers = require('../../../shared/helpers/common.helpers');

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
                    deferred.resolve(convertFromApi(data));
                })
                .catch(function(data) {
                    deferred.reject(convertErrorsFromApi(data));
                });

            return deferred.promise;
        }

        function convertFromApi(data) {
            if (
                commonHelpers.isDefined(data) &&
                commonHelpers.isDefined(data.data) &&
                commonHelpers.isDefined(data.data.details)
            ) {
                data = data.data.data;
                var converted = angular.extend({}, data);
                converted.id = parseInt(data.id);
                converted.parentId = parseInt(data.campaignId);
                converted.campaignId = parseInt(data.campaignId);
                converted.state = constantsHelpers.convertFromName(
                    data.state,
                    constants.settingsState
                );
                converted.status = constantsHelpers.convertFromName(
                    data.status,
                    constants.adGroupRunningStatus
                );
                converted.active = constantsHelpers.convertFromName(
                    data.active,
                    constants.infoboxStatus
                );
                return converted;
            }
        }

        function convertErrorsFromApi(data) {
            var errors;

            if (
                commonHelpers.isDefined(data) &&
                commonHelpers.isDefined(data.data) &&
                commonHelpers.isDefined(data.data.details)
            ) {
                errors = data.data.details;
                return {
                    destinationCampaignId: errors.destinationCampaignId[0],
                    destinationAdGroupName: errors.destinationAdGroupName[0],
                    cloneAds: errors.cloneAds[0],
                    message:
                        data.status === 500 || data.status === 504
                            ? 'Something went wrong'
                            : null,
                };
            }
            return {
                destinationCampaignId: null,
                destinationAdGroupName: null,
                cloneAds: null,
                message:
                    data.status === 500 || data.status === 504
                        ? 'Something went wrong'
                        : null,
            };
        }
    });
