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
        CPC: 'cpc'
    },
    iabCategory: {
        IAB_1: 1,
        IAB_2: 2,
        IAB_3: 3,
        IAB_4: 4,
        IAB_5: 5,
        IAB_6: 6,
        IAB_7: 7,
        IAB_8: 8,
        IAB_9: 9,
        IAB_10: 10,
        IAB_11: 11,
        IAB_12: 12,
        IAB_13: 13,
        IAB_14: 14,
        IAB_15: 15,
        IAB_16: 16,
        IAB_17: 17,
        IAB_18: 18,
        IAB_19: 19,
        IAB_20: 20,
        IAB_21: 21,
        IAB_22: 22,
        IAB_23: 23,
        IAB_24: 24
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
        {name: 'Cost', value: constants.sourceChartMetric.COST},
        {name: 'Avg. CPC', value: constants.sourceChartMetric.CPC}
    ],
    iabCategories: [
        {name: 'Arts & Entertainment', value: constants.iabCategory.IAB_1},
        {name: 'Automotive', value: constants.iabCategory.IAB_2},
        {name: 'Business', value: constants.iabCategory.IAB_3},
        {name: 'Careers', value: constants.iabCategory.IAB_4},
        {name: 'Education', value: constants.iabCategory.IAB_5},
        {name: 'Family & Parenting', value: constants.iabCategory.IAB_6},
        {name: 'Health & Fitness', value: constants.iabCategory.IAB_7},
        {name: 'Food & Drink', value: constants.iabCategory.IAB_8},
        {name: 'Hobbies & Interests', value: constants.iabCategory.IAB_9},
        {name: 'Home & Garden', value: constants.iabCategory.IAB_10},
        {name: 'Law, Government & Politics', value: constants.iabCategory.IAB_11},
        {name: 'News', value: constants.iabCategory.IAB_12},
        {name: 'Personal Finance', value: constants.iabCategory.IAB_13},
        {name: 'Society', value: constants.iabCategory.IAB_14},
        {name: 'Science', value: constants.iabCategory.IAB_15},
        {name: 'Pets', value: constants.iabCategory.IAB_16},
        {name: 'Sports', value: constants.iabCategory.IAB_17},
        {name: 'Style & Fashion', value: constants.iabCategory.IAB_18},
        {name: 'Technology & Computing', value: constants.iabCategory.IAB_19},
        {name: 'Travel', value: constants.iabCategory.IAB_20},
        {name: 'Real Estate', value: constants.iabCategory.IAB_21},
        {name: 'Shopping', value: constants.iabCategory.IAB_22},
        {name: 'Religion & Spirituality', value: constants.iabCategory.IAB_23},
        {name: 'Uncategorized', value: constants.iabCategory.IAB_24}
    ],
    promotionGoals: [
        {name: 'Brand Building', value: constants.promotionGoal.BRAND_BUILDING},
        {name: 'Traffic Acquisition', value: constants.promotionGoal.TRAFFIC_ACQUISITION},
        {name: 'Conversions', value: constants.promotionGoal.CONVERSIONS}
    ]
};
