var constantsHelpers = require('../../../shared/helpers/constants.helpers');

angular
    .module('one.widgets')
    .service('zemCloneContentEndpoint', function($q, $http) {
        this.clone = clone;

        function clone(config) {
            var url = '/rest/internal/contentads/batch/clone/',
                params = convertToApi(config);

            var deferred = $q.defer();
            $http
                .post(url, params)
                .then(function(data) {
                    deferred.resolve(data.data.data);
                })
                .catch(function(data) {
                    deferred.reject(convertErrorsFromApi(data));
                });

            return deferred.promise;
        }

        function convertToApi(config) {
            var converted = {
                adGroupId: config.adGroupId,
                batchId: config.selection.filterId,
                contentAdIds: config.selection.selectedIds,
                deselectedContentAdIds: config.selection.unselectedIds,
                destinationAdGroupId: config.destinationAdGroupId,
                destinationBatchName: config.destinationBatchName,
            };

            if (config.state === true) {
                converted.state = constantsHelpers.convertToName(
                    constants.settingsState.ACTIVE,
                    constants.settingsState
                );
            } else if (config.state === false) {
                converted.state = constantsHelpers.convertToName(
                    constants.settingsState.INACTIVE,
                    constants.settingsState
                );
            } else {
                converted.state = null;
            }

            return converted;
        }

        function convertErrorsFromApi(data) {
            var errors = data.data.details;
            return {
                destinationAdGroupId: errors.destinationAdGroupId
                    ? errors.destinationAdGroupId[0]
                    : null,
                destinationBatchName: errors.destinationBatchName
                    ? errors.destinationBatchName[0]
                    : null,
                destinationCampaignType: errors.type ? errors.type[0] : null,
                message: convertErrorMessage(data, errors),
            };
        }

        function convertErrorMessage(data, errors) {
            switch (data.status) {
                case 500:
                    return 'Something went wrong';
                case 400:
                    return handleBadRequest(errors);
                default:
                    return null;
            }
        }

        function handleBadRequest(errors) {
            if (errors.type) {
                return errors.type[0];
            }
            return null;
        }
    });
