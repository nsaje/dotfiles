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
    },
    sourceChartMetric: {
        CLICKS: 'clicks',
        IMPRESSIONS: 'impressions',
        CTR: 'ctr',
        COST: 'cost',
        CPC: 'cpc',
        CONVERSIONS: 'conversions',
        CONVERSION_RATE: 'conversion_rate'
    },
    iabCategory: {
        IAB1: 'IAB1',
        IAB2: 'IAB2',
        IAB3: 'IAB3',
        IAB4: 'IAB4',
        IAB5: 'IAB5',
        IAB6: 'IAB6',
        IAB7: 'IAB7',
        IAB8: 'IAB8',
        IAB9: 'IAB9',
        IAB10: 'IAB10',
        IAB11: 'IAB11',
        IAB12: 'IAB12',
        IAB13: 'IAB13',
        IAB14: 'IAB14',
        IAB15: 'IAB15',
        IAB16: 'IAB16',
        IAB17: 'IAB17',
        IAB18: 'IAB18',
        IAB19: 'IAB19',
        IAB20: 'IAB20',
        IAB21: 'IAB21',
        IAB22: 'IAB22',
        IAB23: 'IAB23',
        IAB24: 'IAB24'
    },
    promotionGoal: {
        BRAND_BUILDING: 1,
        TRAFFIC_ACQUISITION: 2,
        CONVERSIONS: 3
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
    ],
    sourceChartMetrics: [
        {name: 'Clicks', value: constants.sourceChartMetric.CLICKS},
        {name: 'Impressions', value: constants.sourceChartMetric.IMPRESSIONS},
        {name: 'CTR', value: constants.sourceChartMetric.CTR},
        {name: 'Spend', value: constants.sourceChartMetric.COST},
        {name: 'Avg. CPC', value: constants.sourceChartMetric.CPC}
    ],
    allAccountsChartMetrics: [
        {name: 'Clicks', value: constants.sourceChartMetric.CLICKS},
        {name: 'Spend', value: constants.sourceChartMetric.COST},
        {name: 'Avg. CPC', value: constants.sourceChartMetric.CPC}
    ],
    iabCategories: [
        {name: 'IAB1 - Arts & Entertainment', value: constants.iabCategory.IAB1},
        {name: 'IAB2 - Automotive', value: constants.iabCategory.IAB2},
        {name: 'IAB3 - Business', value: constants.iabCategory.IAB3},
        {name: 'IAB4 - Careers', value: constants.iabCategory.IAB4},
        {name: 'IAB5 - Education', value: constants.iabCategory.IAB5},
        {name: 'IAB6 - Family & Parenting', value: constants.iabCategory.IAB6},
        {name: 'IAB7 - Health & Fitness', value: constants.iabCategory.IAB7},
        {name: 'IAB8 - Food & Drink', value: constants.iabCategory.IAB8},
        {name: 'IAB9 - Hobbies & Interests', value: constants.iabCategory.IAB9},
        {name: 'IAB10 - Home & Garden', value: constants.iabCategory.IAB10},
        {name: 'IAB11 - Law, Government & Politics', value: constants.iabCategory.IAB11},
        {name: 'IAB12 - News', value: constants.iabCategory.IAB12},
        {name: 'IAB13 - Personal Finance', value: constants.iabCategory.IAB13},
        {name: 'IAB14 - Society', value: constants.iabCategory.IAB14},
        {name: 'IAB15 - Science', value: constants.iabCategory.IAB15},
        {name: 'IAB16 - Pets', value: constants.iabCategory.IAB16},
        {name: 'IAB17 - Sports', value: constants.iabCategory.IAB17},
        {name: 'IAB18 - Style & Fashion', value: constants.iabCategory.IAB18},
        {name: 'IAB19 - Technology & Computing', value: constants.iabCategory.IAB19},
        {name: 'IAB20 - Travel', value: constants.iabCategory.IAB20},
        {name: 'IAB21 - Real Estate', value: constants.iabCategory.IAB21},
        {name: 'IAB22 - Shopping', value: constants.iabCategory.IAB22},
        {name: 'IAB23 - Religion & Spirituality', value: constants.iabCategory.IAB23},
        {name: 'IAB24 - Uncategorized', value: constants.iabCategory.IAB24}
    ],
    promotionGoals: [
        {name: 'Brand Building', value: constants.promotionGoal.BRAND_BUILDING},
        {name: 'Traffic Acquisition', value: constants.promotionGoal.TRAFFIC_ACQUISITION},
        {name: 'Conversions', value: constants.promotionGoal.CONVERSIONS}
    ]
};
