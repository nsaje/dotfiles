angular
    .module('one.services')
    .service('zemEntityConverter', function($http, $q, zemUtils) {
        // eslint-disable-line max-len
        //
        // API Converter - converting local entity data to api format and vice-versa (variable format, etc.)
        // TODO: Refactor - Current solution hides mismatch between API and local data, however the best solution
        // would be to minimize the differences and therefor minimize the need of this converter
        //

        this.convertSettingsFromApi = convertSettingsFromApi;
        this.convertSettingsToApi = convertSettingsToApi;
        this.convertValidationErrorsFromApi = convertValidationErrorsFromApi;

        function convertSettingsFromApi(entityType, apiData) {
            var data = zemUtils.convertToCamelCase(apiData);
            if (entityType === constants.entityType.ACCOUNT)
                convertAccountSettingsFromApi(data);
            if (entityType === constants.entityType.CAMPAIGN)
                convertCampaignSettingsFromApi(data);
            if (entityType === constants.entityType.AD_GROUP)
                convertAdGroupSettingsFromApi(data);
            return data;
        }

        function convertSettingsToApi(entityType, data) {
            var apiData = zemUtils.convertToUnderscore(data);
            if (entityType === constants.entityType.ACCOUNT)
                convertAccountSettingsToApi(apiData);
            if (entityType === constants.entityType.CAMPAIGN)
                convertCampaignSettingsToApi(apiData);
            if (entityType === constants.entityType.AD_GROUP)
                convertAdGroupSettingsToApi(apiData);
            return apiData;
        }

        function convertValidationErrorsFromApi(entityType, apiErrors) {
            var errors = zemUtils.convertToCamelCase(apiErrors);
            if (entityType === constants.entityType.AD_GROUP)
                convertAdGroupValidationErrors(errors);
            return errors;
        }

        //
        // Special entity converters - modify data to meet local/api requirements
        //
        function convertAccountSettingsFromApi(data) {
            data.settings.agency = {
                id: data.settings.agency,
                text: data.settings.agency,
            };
        }

        function convertAccountSettingsToApi(apiData) {
            if (apiData.settings.agency)
                apiData.settings.agency = apiData.settings.agency.id;
        }

        function convertCampaignSettingsFromApi(data) {
            data.goals = convertGoalsFromApi(data.goals);
        }

        function convertCampaignSettingsToApi(apiData) {
            // Goals - configure defaults
            apiData.goals = apiData.goals || {};
            apiData.goals.primary = apiData.goals.primary || null;
            apiData.goals.modified = apiData.goals.modified || {};
            apiData.goals.removed = apiData.goals.removed || [];
            apiData.goals.added = apiData.goals.added || [];
        }

        function convertAdGroupSettingsFromApi(data) {
            data.retargetableAdGroups = data.retargetableAdgroups;
            delete data.retargetableAdgroups;

            data.audiences = data.audiences || [];

            // Settings
            var settings = data.settings;
            settings.startDate = settings.startDate
                ? moment(settings.startDate).toDate()
                : null;
            settings.endDate = settings.endDate
                ? moment(settings.endDate).toDate()
                : null;
            settings.manualStop = !settings.endDate;

            settings.cpc = settings.cpcCc;
            settings.dailyBudget = settings.dailyBudgetCc;
            settings.autopilotBudget = settings.autopilotDailyBudget;
            delete settings.cpcCc;
            delete settings.dailyBudgetCc;
            delete settings.autopilotDailyBudget;
        }

        function convertAdGroupSettingsToApi(apiData) {
            var apiSettings = apiData.settings;
            apiSettings.state = apiSettings.state
                ? parseInt(apiSettings.state, 10)
                : null;
            apiSettings.start_date = apiSettings.start_date
                ? moment(apiSettings.start_date).format('YYYY-MM-DD')
                : null;
            apiSettings.end_date = apiSettings.end_date
                ? moment(apiSettings.end_date).format('YYYY-MM-DD')
                : null;

            apiSettings.cpc_cc = apiSettings.cpc;
            apiSettings.daily_budget_cc = apiSettings.daily_budget;
            apiSettings.autopilot_daily_budget = apiSettings.autopilot_budget;
            delete apiSettings.cpc;
            delete apiSettings.daily_budget;
            delete apiSettings.autopilot_budget;

            return apiSettings;
        }

        function convertGoalsFromApi(goals) {
            return (goals || []).map(function(goal) {
                goal.value = goal.values.length
                    ? goal.values[goal.values.length - 1].value
                    : null;
                delete goal.values;
                return goal;
            });
        }

        function convertAdGroupValidationErrors(errors) {
            errors.cpc = errors.cpcCc;
            errors.dailyBudget = errors.dailyBudgetCc;
            errors.autopilotBudget = errors.autopilotDailyBudget;
            delete errors.cpcCc;
            delete errors.dailyBudgetCc;
            delete errors.autopilotDailyBudget;
        }
    });
