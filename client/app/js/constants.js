var constants = {
    adGroupSettingsState: {
        ACTIVE: 1,
        INACTIVE: 2
    },
    adTargetDevice: {
        DESKTOP: 'desktop',
        MOBILE: 'mobile'
    },
    adTargetCountry: {
        AUSTRALIA: 'AU',
        CANADA: 'CA',
        IRELAND: 'IE',
        NEW_ZAELAND: 'NZ',
        UNITED_KINGDOM: 'UK',
        UNITED_STATES: 'US'
    }
};

var options = {
    adGroupSettingsStates: [
        {name: 'Paused', value: constants.adGroupSettingsState.INACTIVE},
        {name: 'Enabled', value: constants.adGroupSettingsState.ACTIVE}
    ],
    adTargetDevices: [
        {name: 'Desktop', value: constants.adTargetDevice.DESKTOP},
        {name: 'Mobile', value: constants.adTargetDevice.MOBILE}
    ],
    adTargetCountries: [
        {name: 'Australia', value: constants.adTargetCountry.AUSTRALIA},
        {name: 'Canada', value: constants.adTargetCountry.CANADA},
        {name: 'Ireland', value: constants.adTargetCountry.IRELAND},
        {name: 'New Zealand', value: constants.adTargetCountry.NEW_ZAELAND},
        {name: 'United Kingdom', value: constants.adTargetCountry.UNITED_KINGDOM},
        {name: 'United States', value: constants.adTargetCountry.UNITED_STATES}
    ]
};
