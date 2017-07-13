angular.module('one.widgets').service('zemCampaignLauncherEndpoint', function ($q, $http) {
    this.validate = validate;
    this.launchCampaign = launchCampaign;

    function validate (account, fields) {
        var deferred = $q.defer();
        var url = '/rest/internal/accounts/' + account.id + '/campaignlauncher/validate';
        $http.post(url, convertFieldsToApi(fields))
            .then(function () {
                deferred.resolve();
            })
            .catch(function (response) {
                deferred.reject(response.data);
            });
        return deferred.promise;
    }

    function launchCampaign (account, fields) {
        var deferred = $q.defer();
        var url = '/rest/internal/accounts/' + account.id + '/campaignlauncher';
        $http.post(url, convertFieldsToApi(fields))
            .then(function (response) {
                deferred.resolve(response.data.data.campaignId);
            })
            .catch(function (response) {
                deferred.reject(response.data);
            });
        return deferred.promise;
    }

    function convertFieldsToApi (fields) {
        var convertedFields = angular.copy(fields);
        convertedFields = convertDateFieldsToApi(convertedFields);
        convertedFields.campaignGoal = convertCampaignGoalFieldToApi(convertedFields.campaignGoal);
        return convertedFields;
    }

    function convertDateFieldsToApi (fields) {
        if (fields.startDate) {
            fields.startDate = moment(fields.startDate).format('YYYY-MM-DD');
        }
        if (fields.endDate) {
            fields.endDate = moment(fields.endDate).format('YYYY-MM-DD');
        }
        return fields;
    }

    function convertCampaignGoalFieldToApi (campaignGoal) {
        if (!campaignGoal) return null;

        // Use "verbose" constant values instead of integers
        var convertedCampaignGoal = angular.copy(campaignGoal);
        angular.forEach(constants.campaignGoalKPI, function (value, key) {
            if (campaignGoal.type === value) {
                convertedCampaignGoal.type = key;
            }
        });

        if (campaignGoal.conversionGoal) {
            angular.forEach(constants.conversionGoalType, function (value, key) {
                if (campaignGoal.conversionGoal.type === value) {
                    convertedCampaignGoal.conversionGoal.type = key;
                }
            });

            angular.forEach(constants.conversionWindow, function (value, key) {
                if (campaignGoal.conversionGoal.conversionWindow === value) {
                    convertedCampaignGoal.conversionGoal.conversionWindow = key;
                }
            });
        }

        return convertedCampaignGoal;
    }
});
