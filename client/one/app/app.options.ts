import {APP_CONSTANTS} from './app.constants';

/**
 * TODO: Move options that are used in Angular app
 * to app.config or to appropriate feature.
 * APP_OPTIONS are used in AngularJS (legacy) app.
 * This file will be deleted, when we will remove AngularJS app.
 */
export const APP_OPTIONS = {
    accountTypes: [
        {name: 'Unknown', value: APP_CONSTANTS.accountTypes.UNKNOWN},
        {name: 'Test', value: APP_CONSTANTS.accountTypes.TEST},
        {name: 'Sandbox', value: APP_CONSTANTS.accountTypes.SANDBOX},
        {name: 'Pilot', value: APP_CONSTANTS.accountTypes.PILOT},
        {name: 'Activated', value: APP_CONSTANTS.accountTypes.ACTIVATED},
        {name: 'Managed', value: APP_CONSTANTS.accountTypes.MANAGED},
        {name: 'PAAS', value: APP_CONSTANTS.accountTypes.PAAS},
    ],
    businesses: [
        {name: 'Z1', value: APP_CONSTANTS.businesses.Z1},
        {name: 'OEN', value: APP_CONSTANTS.businesses.OEN},
        {name: 'ZMS', value: APP_CONSTANTS.businesses.ZMS},
        {name: 'NAS', value: APP_CONSTANTS.businesses.NAS},
        {name: 'INTERNAL', value: APP_CONSTANTS.businesses.INTERNAL},
    ],
    adGroupSettingsStates: [
        {name: 'Paused', value: APP_CONSTANTS.settingsState.INACTIVE},
        {name: 'Enabled', value: APP_CONSTANTS.settingsState.ACTIVE},
    ],
    adGroupSettingsAutopilotStates: [
        {
            name: 'Disabled',
            help: 'Autopilot will not operate on this Ad Group.',
            value: APP_CONSTANTS.adGroupSettingsAutopilotState.INACTIVE,
        },
        {
            name: 'Optimize Bids',
            help:
                'Bids on active Media Sources in this Ad Group will be optimized. ' +
                "Ad Group's Maximum CPC constraint will be enforced.",
            value: APP_CONSTANTS.adGroupSettingsAutopilotState.ACTIVE_CPC,
        },
        {
            name: 'Optimize Bids and Daily Spend Caps',
            help:
                'Both Bids and Daily Spend Caps will be optimized on active Media Sources in this Ad Group.',
            value:
                APP_CONSTANTS.adGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
        },
    ],
    priceDiscoveryOptions: [
        {name: 'Automatic', value: APP_CONSTANTS.priceDiscovery.AUTOMATIC},
        {name: 'Manual', value: APP_CONSTANTS.priceDiscovery.MANUAL},
    ],
    adGroupChartMetrics: [
        {name: 'Clicks', value: APP_CONSTANTS.chartMetric.CLICKS},
        {name: 'Impressions', value: APP_CONSTANTS.chartMetric.IMPRESSIONS},
        {name: 'CTR', value: APP_CONSTANTS.chartMetric.CTR},
        {name: 'Avg. CPC', value: APP_CONSTANTS.chartMetric.CPC},
        {name: 'Avg. CPM', value: APP_CONSTANTS.chartMetric.CPM},
    ],
    adGroupAcquisitionChartPostClickMetrics: [
        {
            name: 'Click Discrepancy',
            value: APP_CONSTANTS.chartMetric.CLICK_DISCREPANCY,
        },
    ],
    adGroupEngagementChartPostClickMetrics: [
        {name: 'Visits', value: APP_CONSTANTS.chartMetric.VISITS},
        {name: 'Pageviews', value: APP_CONSTANTS.chartMetric.PAGEVIEWS},
        {name: 'Unique Users', value: APP_CONSTANTS.chartMetric.UNIQUE_USERS},
        {name: 'New Users', value: APP_CONSTANTS.chartMetric.NEW_USERS},
        {
            name: 'Returning Users',
            value: APP_CONSTANTS.chartMetric.RETURNING_USERS,
        },
        {
            name: '% New Users',
            value: APP_CONSTANTS.chartMetric.PERCENT_NEW_USERS,
        },
        {name: 'Bounce Rate', value: APP_CONSTANTS.chartMetric.BOUNCE_RATE},
        {
            name: 'Pageviews per Visit',
            value: APP_CONSTANTS.chartMetric.PV_PER_VISIT,
        },
        {
            name: 'Bounced Visits',
            value: APP_CONSTANTS.chartMetric.BOUNCED_VISITS,
        },
        {
            name: 'Non-Bounced Visits',
            value: APP_CONSTANTS.chartMetric.NON_BOUNCED_VISITS,
        },
        {name: 'Total Seconds', value: APP_CONSTANTS.chartMetric.TOTAL_SECONDS},
        {name: 'Time on Site', value: APP_CONSTANTS.chartMetric.AVG_TOS},
    ],
    campaignChartMetrics: [
        {name: 'Clicks', value: APP_CONSTANTS.chartMetric.CLICKS},
        {name: 'Impressions', value: APP_CONSTANTS.chartMetric.IMPRESSIONS},
        {name: 'CTR', value: APP_CONSTANTS.chartMetric.CTR},
        {name: 'Avg. CPC', value: APP_CONSTANTS.chartMetric.CPC},
        {name: 'Avg. CPM', value: APP_CONSTANTS.chartMetric.CPM},
    ],
    conversionChartMetrics: [
        {
            name: '',
            value: APP_CONSTANTS.chartMetric.CONVERSION_GOALS_PLACEHOLDER,
            shown: false,
            placeholder: true,
        },
        {
            name: '',
            value: APP_CONSTANTS.chartMetric.PIXELS_PLACEHOLDER,
            shown: false,
            placeholder: true,
        },
    ],
    goalChartMetrics: [
        {
            name: 'Avg. Cost per Minute',
            value: APP_CONSTANTS.chartMetric.COST_PER_MINUTE,
        },
        {
            name: 'Avg. Cost per Pageview',
            value: APP_CONSTANTS.chartMetric.COST_PER_PAGEVIEW,
        },
        {
            name: 'Avg. Cost per Visit',
            value: APP_CONSTANTS.chartMetric.COST_PER_VISIT,
        },
        {
            name: 'Avg. Cost per Non-Bounced Visit',
            value: APP_CONSTANTS.chartMetric.COST_PER_NON_BOUNCED_VISIT,
        },
        {
            name: 'Avg. Cost per New Visitor',
            value: APP_CONSTANTS.chartMetric.COST_PER_NEW_VISITOR,
        },
        {
            name: 'Avg. Cost per Unique User',
            value: APP_CONSTANTS.chartMetric.COST_PER_UNIQUE_USER,
        },
        {
            name: '',
            value:
                APP_CONSTANTS.chartMetric.CONVERSION_GOALS_AVG_COST_PLACEHOLDER,
            shown: false,
            placeholder: true,
        },
        {
            name: '',
            value: APP_CONSTANTS.chartMetric.PIXELS_AVG_COST_PLACEHOLDER,
            shown: false,
            placeholder: true,
        },
    ],
    accountChartMetrics: [
        {name: 'Clicks', value: APP_CONSTANTS.chartMetric.CLICKS},
        {name: 'Impressions', value: APP_CONSTANTS.chartMetric.IMPRESSIONS},
        {name: 'CTR', value: APP_CONSTANTS.chartMetric.CTR},
        {name: 'Avg. CPC', value: APP_CONSTANTS.chartMetric.CPC},
        {name: 'Avg. CPM', value: APP_CONSTANTS.chartMetric.CPM},
    ],
    allAccountsChartMetrics: [
        {name: 'Clicks', value: APP_CONSTANTS.chartMetric.CLICKS},
        {name: 'Impressions', value: APP_CONSTANTS.chartMetric.IMPRESSIONS},
        {name: 'CTR', value: APP_CONSTANTS.chartMetric.CTR},
        {name: 'Avg. CPC', value: APP_CONSTANTS.chartMetric.CPC},
        {name: 'Avg. CPM', value: APP_CONSTANTS.chartMetric.CPM},
    ],
    platformCostChartMetrics: [
        {
            name: 'Data Cost',
            value: APP_CONSTANTS.chartMetric.EFFECTIVE_DATA_COST,
        },
        {
            name: 'Base Data Cost',
            value: APP_CONSTANTS.chartMetric.BASE_EFFECTIVE_DATA_COST,
        },
        {
            name: 'Media Spend',
            value: APP_CONSTANTS.chartMetric.EFFECTIVE_MEDIA_COST,
        },
        {
            name: 'Base Media Spend',
            value: APP_CONSTANTS.chartMetric.BASE_EFFECTIVE_MEDIA_COST,
        },
    ],
    actualCostChartMetrics: [
        {
            name: 'Actual Base Media Spend',
            value: APP_CONSTANTS.chartMetric.MEDIA_COST,
        },
        {
            name: 'Actual Base Data Cost',
            value: APP_CONSTANTS.chartMetric.DATA_COST,
        },
    ],
    languages: [
        {name: 'English', value: APP_CONSTANTS.language.ENGLISH},
        {name: 'German', value: APP_CONSTANTS.language.GERMAN},
        {name: 'Greek', value: APP_CONSTANTS.language.GREEK},
        {name: 'Arabic', value: APP_CONSTANTS.language.ARABIC},
        {name: 'Spanish', value: APP_CONSTANTS.language.SPANISH},
        {name: 'French', value: APP_CONSTANTS.language.FRENCH},
        {name: 'Indonesian', value: APP_CONSTANTS.language.INDONESIAN},
        {name: 'Italian', value: APP_CONSTANTS.language.ITALIAN},
        {name: 'Japanese', value: APP_CONSTANTS.language.JAPANESE},
        {name: 'Malay', value: APP_CONSTANTS.language.MALAY},
        {name: 'Dutch', value: APP_CONSTANTS.language.DUTCH},
        {name: 'Portuguese', value: APP_CONSTANTS.language.PORTUGUESE},
        {name: 'Romanian', value: APP_CONSTANTS.language.ROMANIAN},
        {name: 'Russian', value: APP_CONSTANTS.language.RUSSIAN},
        {name: 'Swedish', value: APP_CONSTANTS.language.SWEDISH},
        {name: 'Turkish', value: APP_CONSTANTS.language.TURKISH},
        {name: 'Vietnamese', value: APP_CONSTANTS.language.VIETNAMESE},
        {
            name: 'Simplified Chinese',
            value: APP_CONSTANTS.language.SIMPLIFIED_CHINESE,
        },
        {
            name: 'Traditional Chinese',
            value: APP_CONSTANTS.language.TRADITIONAL_CHINESE,
        },
        {name: 'Other', value: APP_CONSTANTS.language.OTHER},
    ],
    campaignTypes: [
        {
            name: 'Native Ad Campaign',
            value: APP_CONSTANTS.campaignTypes.CONTENT,
        },
        {
            name: 'Native Video Advertising',
            value: APP_CONSTANTS.campaignTypes.VIDEO,
        },
        {
            name: 'Native Conversion Marketing',
            value: APP_CONSTANTS.campaignTypes.CONVERSION,
        },
        {
            name: 'Native Mobile App Advertising',
            value: APP_CONSTANTS.campaignTypes.MOBILE,
        },
        {
            name: 'Display Ad Campaign',
            value: APP_CONSTANTS.campaignTypes.DISPLAY,
        },
    ],
    iabCategories: [
        {name: 'Uncategorized (IAB24)', value: APP_CONSTANTS.iabCategory.IAB24},
        {
            name: 'Books & Literature (IAB1-1)',
            value: APP_CONSTANTS.iabCategory.IAB1_1,
        },
        {
            name: 'Celebrity Fan/Gossip (IAB1-2)',
            value: APP_CONSTANTS.iabCategory.IAB1_2,
        },
        {name: 'Fine Art (IAB1-3)', value: APP_CONSTANTS.iabCategory.IAB1_3},
        {name: 'Humor (IAB1-4)', value: APP_CONSTANTS.iabCategory.IAB1_4},
        {name: 'Movies (IAB1-5)', value: APP_CONSTANTS.iabCategory.IAB1_5},
        {name: 'Music (IAB1-6)', value: APP_CONSTANTS.iabCategory.IAB1_6},
        {name: 'Television (IAB1-7)', value: APP_CONSTANTS.iabCategory.IAB1_7},
        {name: 'Auto Parts (IAB2-1)', value: APP_CONSTANTS.iabCategory.IAB2_1},
        {name: 'Auto Repair (IAB2-2)', value: APP_CONSTANTS.iabCategory.IAB2_2},
        {
            name: 'Buying/Selling Cars (IAB2-3)',
            value: APP_CONSTANTS.iabCategory.IAB2_3,
        },
        {name: 'Car Culture (IAB2-4)', value: APP_CONSTANTS.iabCategory.IAB2_4},
        {
            name: 'Certified Pre-Owned (IAB2-5)',
            value: APP_CONSTANTS.iabCategory.IAB2_5,
        },
        {name: 'Convertible (IAB2-6)', value: APP_CONSTANTS.iabCategory.IAB2_6},
        {name: 'Coupe (IAB2-7)', value: APP_CONSTANTS.iabCategory.IAB2_7},
        {name: 'Crossover (IAB2-8)', value: APP_CONSTANTS.iabCategory.IAB2_8},
        {name: 'Diesel (IAB2-9)', value: APP_CONSTANTS.iabCategory.IAB2_9},
        {
            name: 'Electric Vehicle (IAB2-10)',
            value: APP_CONSTANTS.iabCategory.IAB2_10,
        },
        {name: 'Hatchback (IAB2-11)', value: APP_CONSTANTS.iabCategory.IAB2_11},
        {name: 'Hybrid (IAB2-12)', value: APP_CONSTANTS.iabCategory.IAB2_12},
        {name: 'Luxury (IAB2-13)', value: APP_CONSTANTS.iabCategory.IAB2_13},
        {name: 'MiniVan (IAB2-14)', value: APP_CONSTANTS.iabCategory.IAB2_14},
        {
            name: 'Mororcycles (IAB2-15)',
            value: APP_CONSTANTS.iabCategory.IAB2_15,
        },
        {
            name: 'Off-Road Vehicles (IAB2-16)',
            value: APP_CONSTANTS.iabCategory.IAB2_16,
        },
        {
            name: 'Performance Vehicles (IAB2-17)',
            value: APP_CONSTANTS.iabCategory.IAB2_17,
        },
        {name: 'Pickup (IAB2-18)', value: APP_CONSTANTS.iabCategory.IAB2_18},
        {
            name: 'Road-Side Assistance (IAB2-19)',
            value: APP_CONSTANTS.iabCategory.IAB2_19,
        },
        {name: 'Sedan (IAB2-20)', value: APP_CONSTANTS.iabCategory.IAB2_20},
        {
            name: 'Trucks & Accessories (IAB2-21)',
            value: APP_CONSTANTS.iabCategory.IAB2_21,
        },
        {
            name: 'Vintage Cars (IAB2-22)',
            value: APP_CONSTANTS.iabCategory.IAB2_22,
        },
        {name: 'Wagon (IAB2-23)', value: APP_CONSTANTS.iabCategory.IAB2_23},
        {name: 'Advertising (IAB3-1)', value: APP_CONSTANTS.iabCategory.IAB3_1},
        {name: 'Agriculture (IAB3-2)', value: APP_CONSTANTS.iabCategory.IAB3_2},
        {
            name: 'Biotech/Biomedical (IAB3-3)',
            value: APP_CONSTANTS.iabCategory.IAB3_3,
        },
        {
            name: 'Business Software (IAB3-4)',
            value: APP_CONSTANTS.iabCategory.IAB3_4,
        },
        {
            name: 'Construction (IAB3-5)',
            value: APP_CONSTANTS.iabCategory.IAB3_5,
        },
        {name: 'Forestry (IAB3-6)', value: APP_CONSTANTS.iabCategory.IAB3_6},
        {name: 'Government (IAB3-7)', value: APP_CONSTANTS.iabCategory.IAB3_7},
        {
            name: 'Green Solutions (IAB3-8)',
            value: APP_CONSTANTS.iabCategory.IAB3_8,
        },
        {
            name: 'Human Resources (IAB3-9)',
            value: APP_CONSTANTS.iabCategory.IAB3_9,
        },
        {name: 'Logistics (IAB3-10)', value: APP_CONSTANTS.iabCategory.IAB3_10},
        {name: 'Marketing (IAB3-11)', value: APP_CONSTANTS.iabCategory.IAB3_11},
        {name: 'Metals (IAB3-12)', value: APP_CONSTANTS.iabCategory.IAB3_12},
        {
            name: 'Career Planning (IAB4-1)',
            value: APP_CONSTANTS.iabCategory.IAB4_1,
        },
        {name: 'College (IAB4-2)', value: APP_CONSTANTS.iabCategory.IAB4_2},
        {
            name: 'Financial Aid (IAB4-3)',
            value: APP_CONSTANTS.iabCategory.IAB4_3,
        },
        {name: 'Job Fairs (IAB4-4)', value: APP_CONSTANTS.iabCategory.IAB4_4},
        {name: 'Job Search (IAB4-5)', value: APP_CONSTANTS.iabCategory.IAB4_5},
        {
            name: 'Resume Writing/Advice (IAB4-6)',
            value: APP_CONSTANTS.iabCategory.IAB4_6,
        },
        {name: 'Nursing (IAB4-7)', value: APP_CONSTANTS.iabCategory.IAB4_7},
        {
            name: 'Scholarships (IAB4-8)',
            value: APP_CONSTANTS.iabCategory.IAB4_8,
        },
        {
            name: 'Telecommuting (IAB4-9)',
            value: APP_CONSTANTS.iabCategory.IAB4_9,
        },
        {
            name: 'U.S. Military (IAB4-10)',
            value: APP_CONSTANTS.iabCategory.IAB4_10,
        },
        {
            name: 'Career Advice (IAB4-11)',
            value: APP_CONSTANTS.iabCategory.IAB4_11,
        },
        {
            name: '7-12 Education (IAB5-1)',
            value: APP_CONSTANTS.iabCategory.IAB5_1,
        },
        {
            name: 'Adult Education (IAB5-2)',
            value: APP_CONSTANTS.iabCategory.IAB5_2,
        },
        {name: 'Art History (IAB5-3)', value: APP_CONSTANTS.iabCategory.IAB5_3},
        {
            name: 'Colledge Administration (IAB5-4)',
            value: APP_CONSTANTS.iabCategory.IAB5_4,
        },
        {
            name: 'College Life (IAB5-5)',
            value: APP_CONSTANTS.iabCategory.IAB5_5,
        },
        {
            name: 'Distance Learning (IAB5-6)',
            value: APP_CONSTANTS.iabCategory.IAB5_6,
        },
        {
            name: 'English as a 2nd Language (IAB5-7)',
            value: APP_CONSTANTS.iabCategory.IAB5_7,
        },
        {
            name: 'Language Learning (IAB5-8)',
            value: APP_CONSTANTS.iabCategory.IAB5_8,
        },
        {
            name: 'Graduate School (IAB5-9)',
            value: APP_CONSTANTS.iabCategory.IAB5_9,
        },
        {
            name: 'Homeschooling (IAB5-10)',
            value: APP_CONSTANTS.iabCategory.IAB5_10,
        },
        {
            name: 'Homework/Study Tips (IAB5-11)',
            value: APP_CONSTANTS.iabCategory.IAB5_11,
        },
        {
            name: 'K-6 Educators (IAB5-12)',
            value: APP_CONSTANTS.iabCategory.IAB5_12,
        },
        {
            name: 'Private School (IAB5-13)',
            value: APP_CONSTANTS.iabCategory.IAB5_13,
        },
        {
            name: 'Special Education (IAB5-14)',
            value: APP_CONSTANTS.iabCategory.IAB5_14,
        },
        {
            name: 'Studying Business (IAB5-15)',
            value: APP_CONSTANTS.iabCategory.IAB5_15,
        },
        {name: 'Adoption (IAB6-1)', value: APP_CONSTANTS.iabCategory.IAB6_1},
        {
            name: 'Babies & Toddlers (IAB6-2)',
            value: APP_CONSTANTS.iabCategory.IAB6_2,
        },
        {
            name: 'Daycare/Pre School (IAB6-3)',
            value: APP_CONSTANTS.iabCategory.IAB6_3,
        },
        {
            name: 'Family Internet (IAB6-4)',
            value: APP_CONSTANTS.iabCategory.IAB6_4,
        },
        {
            name: 'Parenting - K-6 Kids (IAB6-5)',
            value: APP_CONSTANTS.iabCategory.IAB6_5,
        },
        {
            name: 'Parenting teens (IAB6-6)',
            value: APP_CONSTANTS.iabCategory.IAB6_6,
        },
        {name: 'Pregnancy (IAB6-7)', value: APP_CONSTANTS.iabCategory.IAB6_7},
        {
            name: 'Special Needs Kids (IAB6-8)',
            value: APP_CONSTANTS.iabCategory.IAB6_8,
        },
        {name: 'Eldercare (IAB6-9)', value: APP_CONSTANTS.iabCategory.IAB6_9},
        {name: 'Exercise (IAB7-1)', value: APP_CONSTANTS.iabCategory.IAB7_1},
        {name: 'A.D.D. (IAB7-2)', value: APP_CONSTANTS.iabCategory.IAB7_2},
        {name: 'AIDS/HIV (IAB7-3)', value: APP_CONSTANTS.iabCategory.IAB7_3},
        {name: 'Allergies (IAB7-4)', value: APP_CONSTANTS.iabCategory.IAB7_4},
        {
            name: 'Alternative Medicine (IAB7-5)',
            value: APP_CONSTANTS.iabCategory.IAB7_5,
        },
        {name: 'Arthritis (IAB7-6)', value: APP_CONSTANTS.iabCategory.IAB7_6},
        {name: 'Asthma (IAB7-7)', value: APP_CONSTANTS.iabCategory.IAB7_7},
        {name: 'Autism/PDD (IAB7-8)', value: APP_CONSTANTS.iabCategory.IAB7_8},
        {
            name: 'Bipolar Disorder (IAB7-9)',
            value: APP_CONSTANTS.iabCategory.IAB7_9,
        },
        {
            name: 'Brain Tumor (IAB7-10)',
            value: APP_CONSTANTS.iabCategory.IAB7_10,
        },
        {name: 'Cancer (IAB7-11)', value: APP_CONSTANTS.iabCategory.IAB7_11},
        {
            name: 'Cholesterol (IAB7-12)',
            value: APP_CONSTANTS.iabCategory.IAB7_12,
        },
        {
            name: 'Chronic Fatigue Syndrome (IAB7-13)',
            value: APP_CONSTANTS.iabCategory.IAB7_13,
        },
        {
            name: 'Chronic Pain (IAB7-14)',
            value: APP_CONSTANTS.iabCategory.IAB7_14,
        },
        {
            name: 'Cold & Flu (IAB7-15)',
            value: APP_CONSTANTS.iabCategory.IAB7_15,
        },
        {name: 'Deafness (IAB7-16)', value: APP_CONSTANTS.iabCategory.IAB7_16},
        {
            name: 'Dental Care (IAB7-17)',
            value: APP_CONSTANTS.iabCategory.IAB7_17,
        },
        {
            name: 'Depression (IAB7-18)',
            value: APP_CONSTANTS.iabCategory.IAB7_18,
        },
        {
            name: 'Dermatology (IAB7-19)',
            value: APP_CONSTANTS.iabCategory.IAB7_19,
        },
        {name: 'Diabetes (IAB7-20)', value: APP_CONSTANTS.iabCategory.IAB7_20},
        {name: 'Epilepsy (IAB7-21)', value: APP_CONSTANTS.iabCategory.IAB7_21},
        {
            name: 'GERD/Acid Reflux (IAB7-22)',
            value: APP_CONSTANTS.iabCategory.IAB7_22,
        },
        {
            name: 'Headaches/Migraines (IAB7-23)',
            value: APP_CONSTANTS.iabCategory.IAB7_23,
        },
        {
            name: 'Heart Disease (IAB7-24)',
            value: APP_CONSTANTS.iabCategory.IAB7_24,
        },
        {
            name: 'Herbs for Health (IAB7-25)',
            value: APP_CONSTANTS.iabCategory.IAB7_25,
        },
        {
            name: 'Holistic Healing (IAB7-26)',
            value: APP_CONSTANTS.iabCategory.IAB7_26,
        },
        {
            name: "IBS/Crohn's Disease (IAB7-27)",
            value: APP_CONSTANTS.iabCategory.IAB7_27,
        },
        {
            name: 'Incest/Abuse Support (IAB7-28)',
            value: APP_CONSTANTS.iabCategory.IAB7_28,
        },
        {
            name: 'Incontinence (IAB7-29)',
            value: APP_CONSTANTS.iabCategory.IAB7_29,
        },
        {
            name: 'Infertility (IAB7-30)',
            value: APP_CONSTANTS.iabCategory.IAB7_30,
        },
        {
            name: "Men's Health (IAB7-31)",
            value: APP_CONSTANTS.iabCategory.IAB7_31,
        },
        {name: 'Nutrition (IAB7-32)', value: APP_CONSTANTS.iabCategory.IAB7_32},
        {
            name: 'Orthopedics (IAB7-33)',
            value: APP_CONSTANTS.iabCategory.IAB7_33,
        },
        {
            name: 'Panic/Anxiety Disorders (IAB7-34)',
            value: APP_CONSTANTS.iabCategory.IAB7_34,
        },
        {
            name: 'Pediatrics (IAB7-35)',
            value: APP_CONSTANTS.iabCategory.IAB7_35,
        },
        {
            name: 'Physical Therapy (IAB7-36)',
            value: APP_CONSTANTS.iabCategory.IAB7_36,
        },
        {
            name: 'Psychology/Psychiatry (IAB7-37)',
            value: APP_CONSTANTS.iabCategory.IAB7_37,
        },
        {
            name: 'Senior Health (IAB7-38)',
            value: APP_CONSTANTS.iabCategory.IAB7_38,
        },
        {name: 'Sexuality (IAB7-39)', value: APP_CONSTANTS.iabCategory.IAB7_39},
        {
            name: 'Sleep Disorders (IAB7-40)',
            value: APP_CONSTANTS.iabCategory.IAB7_40,
        },
        {
            name: 'Smoking Cessation (IAB7-41)',
            value: APP_CONSTANTS.iabCategory.IAB7_41,
        },
        {
            name: 'Substance Abuse (IAB7-42)',
            value: APP_CONSTANTS.iabCategory.IAB7_42,
        },
        {
            name: 'Thyroid Disease (IAB7-43)',
            value: APP_CONSTANTS.iabCategory.IAB7_43,
        },
        {
            name: 'Weight Loss (IAB7-44)',
            value: APP_CONSTANTS.iabCategory.IAB7_44,
        },
        {
            name: "Women's Health (IAB7-45)",
            value: APP_CONSTANTS.iabCategory.IAB7_45,
        },
        {
            name: 'American Cuisine (IAB8-1)',
            value: APP_CONSTANTS.iabCategory.IAB8_1,
        },
        {
            name: 'Barbecues & Grilling (IAB8-2)',
            value: APP_CONSTANTS.iabCategory.IAB8_2,
        },
        {
            name: 'Cajun/Creole (IAB8-3)',
            value: APP_CONSTANTS.iabCategory.IAB8_3,
        },
        {
            name: 'Chinese Cuisine (IAB8-4)',
            value: APP_CONSTANTS.iabCategory.IAB8_4,
        },
        {
            name: 'Cocktails/Beer (IAB8-5)',
            value: APP_CONSTANTS.iabCategory.IAB8_5,
        },
        {name: 'Coffee/Tea (IAB8-6)', value: APP_CONSTANTS.iabCategory.IAB8_6},
        {
            name: 'Cuisine-Specific (IAB8-7)',
            value: APP_CONSTANTS.iabCategory.IAB8_7,
        },
        {
            name: 'Desserts & Baking (IAB8-8)',
            value: APP_CONSTANTS.iabCategory.IAB8_8,
        },
        {name: 'Dining Out (IAB8-9)', value: APP_CONSTANTS.iabCategory.IAB8_9},
        {
            name: 'Food Allergies (IAB8-10)',
            value: APP_CONSTANTS.iabCategory.IAB8_10,
        },
        {
            name: 'French Cuisine (IAB8-11)',
            value: APP_CONSTANTS.iabCategory.IAB8_11,
        },
        {
            name: 'Health/Lowfat Cooking (IAB8-12)',
            value: APP_CONSTANTS.iabCategory.IAB8_12,
        },
        {
            name: 'Italian Cuisine (IAB8-13)',
            value: APP_CONSTANTS.iabCategory.IAB8_13,
        },
        {
            name: 'Japanese Cuisine (IAB8-14)',
            value: APP_CONSTANTS.iabCategory.IAB8_14,
        },
        {
            name: 'Mexican Cuisine (IAB8-15)',
            value: APP_CONSTANTS.iabCategory.IAB8_15,
        },
        {name: 'Vegan (IAB8-16)', value: APP_CONSTANTS.iabCategory.IAB8_16},
        {
            name: 'Vegetarian (IAB8-17)',
            value: APP_CONSTANTS.iabCategory.IAB8_17,
        },
        {name: 'Wine (IAB8-18)', value: APP_CONSTANTS.iabCategory.IAB8_18},
        {
            name: 'Art/Technology (IAB9-1)',
            value: APP_CONSTANTS.iabCategory.IAB9_1,
        },
        {
            name: 'Arts & Crafts (IAB9-2)',
            value: APP_CONSTANTS.iabCategory.IAB9_2,
        },
        {name: 'Beadwork (IAB9-3)', value: APP_CONSTANTS.iabCategory.IAB9_3},
        {
            name: 'Birdwatching (IAB9-4)',
            value: APP_CONSTANTS.iabCategory.IAB9_4,
        },
        {
            name: 'Board Games/Puzzles (IAB9-5)',
            value: APP_CONSTANTS.iabCategory.IAB9_5,
        },
        {
            name: 'Candle & Soap Making (IAB9-6)',
            value: APP_CONSTANTS.iabCategory.IAB9_6,
        },
        {name: 'Card Games (IAB9-7)', value: APP_CONSTANTS.iabCategory.IAB9_7},
        {name: 'Chess (IAB9-8)', value: APP_CONSTANTS.iabCategory.IAB9_8},
        {name: 'Cigars (IAB9-9)', value: APP_CONSTANTS.iabCategory.IAB9_9},
        {
            name: 'Collecting (IAB9-10)',
            value: APP_CONSTANTS.iabCategory.IAB9_10,
        },
        {
            name: 'Comic Books (IAB9-11)',
            value: APP_CONSTANTS.iabCategory.IAB9_11,
        },
        {
            name: 'Drawing/Sketching (IAB9-12)',
            value: APP_CONSTANTS.iabCategory.IAB9_12,
        },
        {
            name: 'Freelance Writing (IAB9-13)',
            value: APP_CONSTANTS.iabCategory.IAB9_13,
        },
        {name: 'Genealogy (IAB9-14)', value: APP_CONSTANTS.iabCategory.IAB9_14},
        {
            name: 'Getting Published (IAB9-15)',
            value: APP_CONSTANTS.iabCategory.IAB9_15,
        },
        {name: 'Guitar (IAB9-16)', value: APP_CONSTANTS.iabCategory.IAB9_16},
        {
            name: 'Home Recording (IAB9-17)',
            value: APP_CONSTANTS.iabCategory.IAB9_17,
        },
        {
            name: 'Investors & Patents (IAB9-18)',
            value: APP_CONSTANTS.iabCategory.IAB9_18,
        },
        {
            name: 'Jewelry Making (IAB9-19)',
            value: APP_CONSTANTS.iabCategory.IAB9_19,
        },
        {
            name: 'Magic & Illusion (IAB9-20)',
            value: APP_CONSTANTS.iabCategory.IAB9_20,
        },
        {
            name: 'Needlework (IAB9-21)',
            value: APP_CONSTANTS.iabCategory.IAB9_21,
        },
        {name: 'Painting (IAB9-22)', value: APP_CONSTANTS.iabCategory.IAB9_22},
        {
            name: 'Photography (IAB9-23)',
            value: APP_CONSTANTS.iabCategory.IAB9_23,
        },
        {name: 'Radio (IAB9-24)', value: APP_CONSTANTS.iabCategory.IAB9_24},
        {
            name: 'Roleplaying Games (IAB9-25)',
            value: APP_CONSTANTS.iabCategory.IAB9_25,
        },
        {
            name: 'Sci-Fi & Fantasy (IAB9-26)',
            value: APP_CONSTANTS.iabCategory.IAB9_26,
        },
        {
            name: 'Scrapbooking (IAB9-27)',
            value: APP_CONSTANTS.iabCategory.IAB9_27,
        },
        {
            name: 'Screenwriting (IAB9-28)',
            value: APP_CONSTANTS.iabCategory.IAB9_28,
        },
        {
            name: 'Stamps & Coins (IAB9-29)',
            value: APP_CONSTANTS.iabCategory.IAB9_29,
        },
        {
            name: 'Video & Computer Games (IAB9-30)',
            value: APP_CONSTANTS.iabCategory.IAB9_30,
        },
        {
            name: 'Woodworking (IAB9-31)',
            value: APP_CONSTANTS.iabCategory.IAB9_31,
        },
        {
            name: 'Appliances (IAB10-1)',
            value: APP_CONSTANTS.iabCategory.IAB10_1,
        },
        {
            name: 'Entertaining (IAB10-2)',
            value: APP_CONSTANTS.iabCategory.IAB10_2,
        },
        {
            name: 'Environmental Safety (IAB10-3)',
            value: APP_CONSTANTS.iabCategory.IAB10_3,
        },
        {name: 'Gardening (IAB10-4)', value: APP_CONSTANTS.iabCategory.IAB10_4},
        {
            name: 'Home Repair (IAB10-5)',
            value: APP_CONSTANTS.iabCategory.IAB10_5,
        },
        {
            name: 'Home Theater (IAB10-6)',
            value: APP_CONSTANTS.iabCategory.IAB10_6,
        },
        {
            name: 'Interior Decorating (IAB10-7)',
            value: APP_CONSTANTS.iabCategory.IAB10_7,
        },
        {
            name: 'Landscaping (IAB10-8)',
            value: APP_CONSTANTS.iabCategory.IAB10_8,
        },
        {
            name: 'Remodeling & Construction (IAB10-9)',
            value: APP_CONSTANTS.iabCategory.IAB10_9,
        },
        {
            name: 'Immigration (IAB11-1)',
            value: APP_CONSTANTS.iabCategory.IAB11_1,
        },
        {
            name: 'Legal Issues (IAB11-2)',
            value: APP_CONSTANTS.iabCategory.IAB11_2,
        },
        {
            name: 'U.S. Government Resources (IAB11-3)',
            value: APP_CONSTANTS.iabCategory.IAB11_3,
        },
        {name: 'Politics (IAB11-4)', value: APP_CONSTANTS.iabCategory.IAB11_4},
        {
            name: 'Commentary (IAB11-5)',
            value: APP_CONSTANTS.iabCategory.IAB11_5,
        },
        {
            name: 'International News (IAB12-1)',
            value: APP_CONSTANTS.iabCategory.IAB12_1,
        },
        {
            name: 'National News (IAB12-2)',
            value: APP_CONSTANTS.iabCategory.IAB12_2,
        },
        {
            name: 'Local News (IAB12-3)',
            value: APP_CONSTANTS.iabCategory.IAB12_3,
        },
        {
            name: 'Beginning Investing (IAB13-1)',
            value: APP_CONSTANTS.iabCategory.IAB13_1,
        },
        {
            name: 'Credit/Debt & Loans (IAB13-2)',
            value: APP_CONSTANTS.iabCategory.IAB13_2,
        },
        {
            name: 'Financial News (IAB13-3)',
            value: APP_CONSTANTS.iabCategory.IAB13_3,
        },
        {
            name: 'Financial Planning (IAB13-4)',
            value: APP_CONSTANTS.iabCategory.IAB13_4,
        },
        {
            name: 'Hedge Fund (IAB13-5)',
            value: APP_CONSTANTS.iabCategory.IAB13_5,
        },
        {name: 'Insurance (IAB13-6)', value: APP_CONSTANTS.iabCategory.IAB13_6},
        {name: 'Investing (IAB13-7)', value: APP_CONSTANTS.iabCategory.IAB13_7},
        {
            name: 'Mutual Funds (IAB13-8)',
            value: APP_CONSTANTS.iabCategory.IAB13_8,
        },
        {name: 'Options (IAB13-9)', value: APP_CONSTANTS.iabCategory.IAB13_9},
        {
            name: 'Retirement Planning (IAB13-10)',
            value: APP_CONSTANTS.iabCategory.IAB13_10,
        },
        {name: 'Stocks (IAB13-11)', value: APP_CONSTANTS.iabCategory.IAB13_11},
        {
            name: 'Tax Planning (IAB13-12)',
            value: APP_CONSTANTS.iabCategory.IAB13_12,
        },
        {name: 'Dating (IAB14-1)', value: APP_CONSTANTS.iabCategory.IAB14_1},
        {
            name: 'Divorce Support (IAB14-2)',
            value: APP_CONSTANTS.iabCategory.IAB14_2,
        },
        {name: 'Gay Life (IAB14-3)', value: APP_CONSTANTS.iabCategory.IAB14_3},
        {name: 'Marriage (IAB14-4)', value: APP_CONSTANTS.iabCategory.IAB14_4},
        {
            name: 'Senior Living (IAB14-5)',
            value: APP_CONSTANTS.iabCategory.IAB14_5,
        },
        {name: 'Teens (IAB14-6)', value: APP_CONSTANTS.iabCategory.IAB14_6},
        {name: 'Weddings (IAB14-7)', value: APP_CONSTANTS.iabCategory.IAB14_7},
        {
            name: 'Ethnic Specific (IAB14-8)',
            value: APP_CONSTANTS.iabCategory.IAB14_8,
        },
        {name: 'Astrology (IAB15-1)', value: APP_CONSTANTS.iabCategory.IAB15_1},
        {name: 'Biology (IAB15-2)', value: APP_CONSTANTS.iabCategory.IAB15_2},
        {name: 'Chemistry (IAB15-3)', value: APP_CONSTANTS.iabCategory.IAB15_3},
        {name: 'Geology (IAB15-4)', value: APP_CONSTANTS.iabCategory.IAB15_4},
        {
            name: 'Paranormal Phenomena (IAB15-5)',
            value: APP_CONSTANTS.iabCategory.IAB15_5,
        },
        {name: 'Physics (IAB15-6)', value: APP_CONSTANTS.iabCategory.IAB15_6},
        {
            name: 'Space/Astronomy (IAB15-7)',
            value: APP_CONSTANTS.iabCategory.IAB15_7,
        },
        {name: 'Geography (IAB15-8)', value: APP_CONSTANTS.iabCategory.IAB15_8},
        {name: 'Botany (IAB15-9)', value: APP_CONSTANTS.iabCategory.IAB15_9},
        {name: 'Weather (IAB15-10)', value: APP_CONSTANTS.iabCategory.IAB15_10},
        {name: 'Aquariums (IAB16-1)', value: APP_CONSTANTS.iabCategory.IAB16_1},
        {name: 'Birds (IAB16-2)', value: APP_CONSTANTS.iabCategory.IAB16_2},
        {name: 'Cats (IAB16-3)', value: APP_CONSTANTS.iabCategory.IAB16_3},
        {name: 'Dogs (IAB16-4)', value: APP_CONSTANTS.iabCategory.IAB16_4},
        {
            name: 'Large Animals (IAB16-5)',
            value: APP_CONSTANTS.iabCategory.IAB16_5,
        },
        {name: 'Reptiles (IAB16-6)', value: APP_CONSTANTS.iabCategory.IAB16_6},
        {
            name: 'Veterinary Medicine (IAB16-7)',
            value: APP_CONSTANTS.iabCategory.IAB16_7,
        },
        {
            name: 'Auto Racing (IAB17-1)',
            value: APP_CONSTANTS.iabCategory.IAB17_1,
        },
        {name: 'Baseball (IAB17-2)', value: APP_CONSTANTS.iabCategory.IAB17_2},
        {name: 'Bicycling (IAB17-3)', value: APP_CONSTANTS.iabCategory.IAB17_3},
        {
            name: 'Bodybuilding (IAB17-4)',
            value: APP_CONSTANTS.iabCategory.IAB17_4,
        },
        {name: 'Boxing (IAB17-5)', value: APP_CONSTANTS.iabCategory.IAB17_5},
        {
            name: 'Canoeing/Kayaking (IAB17-6)',
            value: APP_CONSTANTS.iabCategory.IAB17_6,
        },
        {
            name: 'Cheerleading (IAB17-7)',
            value: APP_CONSTANTS.iabCategory.IAB17_7,
        },
        {name: 'Climbing (IAB17-8)', value: APP_CONSTANTS.iabCategory.IAB17_8},
        {name: 'Cricket (IAB17-9)', value: APP_CONSTANTS.iabCategory.IAB17_9},
        {
            name: 'Figure Skating (IAB17-10)',
            value: APP_CONSTANTS.iabCategory.IAB17_10,
        },
        {
            name: 'Fly Fishing (IAB17-11)',
            value: APP_CONSTANTS.iabCategory.IAB17_11,
        },
        {
            name: 'Football (IAB17-12)',
            value: APP_CONSTANTS.iabCategory.IAB17_12,
        },
        {
            name: 'Freshwater Fishing (IAB17-13)',
            value: APP_CONSTANTS.iabCategory.IAB17_13,
        },
        {
            name: 'Game & Fish (IAB17-14)',
            value: APP_CONSTANTS.iabCategory.IAB17_14,
        },
        {name: 'Golf (IAB17-15)', value: APP_CONSTANTS.iabCategory.IAB17_15},
        {
            name: 'Horse Racing (IAB17-16)',
            value: APP_CONSTANTS.iabCategory.IAB17_16,
        },
        {name: 'Horses (IAB17-17)', value: APP_CONSTANTS.iabCategory.IAB17_17},
        {
            name: 'Hunting/Shooting (IAB17-18)',
            value: APP_CONSTANTS.iabCategory.IAB17_18,
        },
        {
            name: 'Inline Skating (IAB17-19)',
            value: APP_CONSTANTS.iabCategory.IAB17_19,
        },
        {
            name: 'Martial Arts (IAB17-20)',
            value: APP_CONSTANTS.iabCategory.IAB17_20,
        },
        {
            name: 'Mountain Biking (IAB17-21)',
            value: APP_CONSTANTS.iabCategory.IAB17_21,
        },
        {
            name: 'NASCAR Racing (IAB17-22)',
            value: APP_CONSTANTS.iabCategory.IAB17_22,
        },
        {
            name: 'Olympics (IAB17-23)',
            value: APP_CONSTANTS.iabCategory.IAB17_23,
        },
        {
            name: 'Paintball (IAB17-24)',
            value: APP_CONSTANTS.iabCategory.IAB17_24,
        },
        {
            name: 'Power & Motorcycles (IAB17-25)',
            value: APP_CONSTANTS.iabCategory.IAB17_25,
        },
        {
            name: 'Pro Basketball (IAB17-26)',
            value: APP_CONSTANTS.iabCategory.IAB17_26,
        },
        {
            name: 'Pro Ice Hockey (IAB17-27)',
            value: APP_CONSTANTS.iabCategory.IAB17_27,
        },
        {name: 'Rodeo (IAB17-28)', value: APP_CONSTANTS.iabCategory.IAB17_28},
        {name: 'Rugby (IAB17-29)', value: APP_CONSTANTS.iabCategory.IAB17_29},
        {
            name: 'Running/Jogging (IAB17-30)',
            value: APP_CONSTANTS.iabCategory.IAB17_30,
        },
        {name: 'Sailing (IAB17-31)', value: APP_CONSTANTS.iabCategory.IAB17_31},
        {
            name: 'Saltwater Fishing (IAB17-32)',
            value: APP_CONSTANTS.iabCategory.IAB17_32,
        },
        {
            name: 'Scuba Diving (IAB17-33)',
            value: APP_CONSTANTS.iabCategory.IAB17_33,
        },
        {
            name: 'Skateboarding (IAB17-34)',
            value: APP_CONSTANTS.iabCategory.IAB17_34,
        },
        {name: 'Skiing (IAB17-35)', value: APP_CONSTANTS.iabCategory.IAB17_35},
        {
            name: 'Snowboarding (IAB17-36)',
            value: APP_CONSTANTS.iabCategory.IAB17_36,
        },
        {
            name: 'Surfing/Bodyboarding (IAB17-37)',
            value: APP_CONSTANTS.iabCategory.IAB17_37,
        },
        {
            name: 'Swimming (IAB17-38)',
            value: APP_CONSTANTS.iabCategory.IAB17_38,
        },
        {
            name: 'Table Tennis/Ping-Pong (IAB17-39)',
            value: APP_CONSTANTS.iabCategory.IAB17_39,
        },
        {name: 'Tennis (IAB17-40)', value: APP_CONSTANTS.iabCategory.IAB17_40},
        {
            name: 'Volleyball (IAB17-41)',
            value: APP_CONSTANTS.iabCategory.IAB17_41,
        },
        {name: 'Walking (IAB17-42)', value: APP_CONSTANTS.iabCategory.IAB17_42},
        {
            name: 'Waterski/Wakeboard (IAB17-43)',
            value: APP_CONSTANTS.iabCategory.IAB17_43,
        },
        {
            name: 'World Soccer (IAB17-44)',
            value: APP_CONSTANTS.iabCategory.IAB17_44,
        },
        {name: 'Beauty (IAB18-1)', value: APP_CONSTANTS.iabCategory.IAB18_1},
        {name: 'Body Art (IAB18-2)', value: APP_CONSTANTS.iabCategory.IAB18_2},
        {name: 'Fashion (IAB18-3)', value: APP_CONSTANTS.iabCategory.IAB18_3},
        {name: 'Jewelry (IAB18-4)', value: APP_CONSTANTS.iabCategory.IAB18_4},
        {name: 'Clothing (IAB18-5)', value: APP_CONSTANTS.iabCategory.IAB18_5},
        {
            name: 'Accessories (IAB18-6)',
            value: APP_CONSTANTS.iabCategory.IAB18_6,
        },
        {
            name: '3-D Graphics (IAB19-1)',
            value: APP_CONSTANTS.iabCategory.IAB19_1,
        },
        {name: 'Animation (IAB19-2)', value: APP_CONSTANTS.iabCategory.IAB19_2},
        {
            name: 'Antivirus Software (IAB19-3)',
            value: APP_CONSTANTS.iabCategory.IAB19_3,
        },
        {name: 'C/C++ (IAB19-4)', value: APP_CONSTANTS.iabCategory.IAB19_4},
        {
            name: 'Cameras & Camcorders (IAB19-5)',
            value: APP_CONSTANTS.iabCategory.IAB19_5,
        },
        {
            name: 'Cell Phones (IAB19-6)',
            value: APP_CONSTANTS.iabCategory.IAB19_6,
        },
        {
            name: 'Computer Certification (IAB19-7)',
            value: APP_CONSTANTS.iabCategory.IAB19_7,
        },
        {
            name: 'Computer Networking (IAB19-8)',
            value: APP_CONSTANTS.iabCategory.IAB19_8,
        },
        {
            name: 'Computer Peripherals (IAB19-9)',
            value: APP_CONSTANTS.iabCategory.IAB19_9,
        },
        {
            name: 'Computer Reviews (IAB19-10)',
            value: APP_CONSTANTS.iabCategory.IAB19_10,
        },
        {
            name: 'Data Centers (IAB19-11)',
            value: APP_CONSTANTS.iabCategory.IAB19_11,
        },
        {
            name: 'Databases (IAB19-12)',
            value: APP_CONSTANTS.iabCategory.IAB19_12,
        },
        {
            name: 'Desktop Publishing (IAB19-13)',
            value: APP_CONSTANTS.iabCategory.IAB19_13,
        },
        {
            name: 'Desktop Video (IAB19-14)',
            value: APP_CONSTANTS.iabCategory.IAB19_14,
        },
        {name: 'Email (IAB19-15)', value: APP_CONSTANTS.iabCategory.IAB19_15},
        {
            name: 'Graphics Software (IAB19-16)',
            value: APP_CONSTANTS.iabCategory.IAB19_16,
        },
        {
            name: 'Home Video/DVD (IAB19-17)',
            value: APP_CONSTANTS.iabCategory.IAB19_17,
        },
        {
            name: 'Internet Technology (IAB19-18)',
            value: APP_CONSTANTS.iabCategory.IAB19_18,
        },
        {name: 'Java (IAB19-19)', value: APP_CONSTANTS.iabCategory.IAB19_19},
        {
            name: 'JavaScript (IAB19-20)',
            value: APP_CONSTANTS.iabCategory.IAB19_20,
        },
        {
            name: 'Mac Support (IAB19-21)',
            value: APP_CONSTANTS.iabCategory.IAB19_21,
        },
        {
            name: 'MP3/MIDI (IAB19-22)',
            value: APP_CONSTANTS.iabCategory.IAB19_22,
        },
        {
            name: 'Net Conferencing (IAB19-23)',
            value: APP_CONSTANTS.iabCategory.IAB19_23,
        },
        {
            name: 'Net for Beginners (IAB19-24)',
            value: APP_CONSTANTS.iabCategory.IAB19_24,
        },
        {
            name: 'Network Security (IAB19-25)',
            value: APP_CONSTANTS.iabCategory.IAB19_25,
        },
        {
            name: 'Palmtops/PDAs (IAB19-26)',
            value: APP_CONSTANTS.iabCategory.IAB19_26,
        },
        {
            name: 'PC Support (IAB19-27)',
            value: APP_CONSTANTS.iabCategory.IAB19_27,
        },
        {
            name: 'Portable (IAB19-28)',
            value: APP_CONSTANTS.iabCategory.IAB19_28,
        },
        {
            name: 'Entertainment (IAB19-29)',
            value: APP_CONSTANTS.iabCategory.IAB19_29,
        },
        {
            name: 'Shareware/Freeware (IAB19-30)',
            value: APP_CONSTANTS.iabCategory.IAB19_30,
        },
        {name: 'Unix (IAB19-31)', value: APP_CONSTANTS.iabCategory.IAB19_31},
        {
            name: 'Visual Basic (IAB19-32)',
            value: APP_CONSTANTS.iabCategory.IAB19_32,
        },
        {
            name: 'Web Clip Art (IAB19-33)',
            value: APP_CONSTANTS.iabCategory.IAB19_33,
        },
        {
            name: 'Web Design/HTML (IAB19-34)',
            value: APP_CONSTANTS.iabCategory.IAB19_34,
        },
        {
            name: 'Web Search (IAB19-35)',
            value: APP_CONSTANTS.iabCategory.IAB19_35,
        },
        {name: 'Windows (IAB19-36)', value: APP_CONSTANTS.iabCategory.IAB19_36},
        {
            name: 'Adventure Travel (IAB20-1)',
            value: APP_CONSTANTS.iabCategory.IAB20_1,
        },
        {name: 'Africa (IAB20-2)', value: APP_CONSTANTS.iabCategory.IAB20_2},
        {
            name: 'Air Travel (IAB20-3)',
            value: APP_CONSTANTS.iabCategory.IAB20_3,
        },
        {
            name: 'Australia & New Zealand (IAB20-4)',
            value: APP_CONSTANTS.iabCategory.IAB20_4,
        },
        {
            name: 'Bed & Breakfasts (IAB20-5)',
            value: APP_CONSTANTS.iabCategory.IAB20_5,
        },
        {
            name: 'Budget Travel (IAB20-6)',
            value: APP_CONSTANTS.iabCategory.IAB20_6,
        },
        {
            name: 'Business Travel (IAB20-7)',
            value: APP_CONSTANTS.iabCategory.IAB20_7,
        },
        {
            name: 'By US Locale (IAB20-8)',
            value: APP_CONSTANTS.iabCategory.IAB20_8,
        },
        {name: 'Camping (IAB20-9)', value: APP_CONSTANTS.iabCategory.IAB20_9},
        {name: 'Canada (IAB20-10)', value: APP_CONSTANTS.iabCategory.IAB20_10},
        {
            name: 'Caribbean (IAB20-11)',
            value: APP_CONSTANTS.iabCategory.IAB20_11,
        },
        {name: 'Cruises (IAB20-12)', value: APP_CONSTANTS.iabCategory.IAB20_12},
        {
            name: 'Eastern Europe (IAB20-13)',
            value: APP_CONSTANTS.iabCategory.IAB20_13,
        },
        {name: 'Europe (IAB20-14)', value: APP_CONSTANTS.iabCategory.IAB20_14},
        {name: 'France (IAB20-15)', value: APP_CONSTANTS.iabCategory.IAB20_15},
        {name: 'Greece (IAB20-16)', value: APP_CONSTANTS.iabCategory.IAB20_16},
        {
            name: 'Honeymoons/Getaways (IAB20-17)',
            value: APP_CONSTANTS.iabCategory.IAB20_17,
        },
        {name: 'Hotels (IAB20-18)', value: APP_CONSTANTS.iabCategory.IAB20_18},
        {name: 'Italy (IAB20-19)', value: APP_CONSTANTS.iabCategory.IAB20_19},
        {name: 'Japan (IAB20-20)', value: APP_CONSTANTS.iabCategory.IAB20_20},
        {
            name: 'Mexico & Central America (IAB20-21)',
            value: APP_CONSTANTS.iabCategory.IAB20_21,
        },
        {
            name: 'National Parks (IAB20-22)',
            value: APP_CONSTANTS.iabCategory.IAB20_22,
        },
        {
            name: 'South America (IAB20-23)',
            value: APP_CONSTANTS.iabCategory.IAB20_23,
        },
        {name: 'Spas (IAB20-24)', value: APP_CONSTANTS.iabCategory.IAB20_24},
        {
            name: 'Theme Parks (IAB20-25)',
            value: APP_CONSTANTS.iabCategory.IAB20_25,
        },
        {
            name: 'Traveling with Kids (IAB20-26)',
            value: APP_CONSTANTS.iabCategory.IAB20_26,
        },
        {
            name: 'United Kingdom (IAB20-27)',
            value: APP_CONSTANTS.iabCategory.IAB20_27,
        },
        {
            name: 'Apartments (IAB21-1)',
            value: APP_CONSTANTS.iabCategory.IAB21_1,
        },
        {
            name: 'Architects (IAB21-2)',
            value: APP_CONSTANTS.iabCategory.IAB21_2,
        },
        {
            name: 'Buying/Selling Homes (IAB21-3)',
            value: APP_CONSTANTS.iabCategory.IAB21_3,
        },
        {
            name: 'Contests & Freebies (IAB22-1)',
            value: APP_CONSTANTS.iabCategory.IAB22_1,
        },
        {name: 'Couponing (IAB22-2)', value: APP_CONSTANTS.iabCategory.IAB22_2},
        {
            name: 'Comparison (IAB22-3)',
            value: APP_CONSTANTS.iabCategory.IAB22_3,
        },
        {name: 'Engines (IAB22-4)', value: APP_CONSTANTS.iabCategory.IAB22_4},
        {
            name: 'Alternative Religions (IAB23-1)',
            value: APP_CONSTANTS.iabCategory.IAB23_1,
        },
        {
            name: 'Atheism/Agnosticism (IAB23-2)',
            value: APP_CONSTANTS.iabCategory.IAB23_2,
        },
        {name: 'Buddhism (IAB23-3)', value: APP_CONSTANTS.iabCategory.IAB23_3},
        {
            name: 'Catholicism (IAB23-4)',
            value: APP_CONSTANTS.iabCategory.IAB23_4,
        },
        {
            name: 'Christianity (IAB23-5)',
            value: APP_CONSTANTS.iabCategory.IAB23_5,
        },
        {name: 'Hinduism (IAB23-6)', value: APP_CONSTANTS.iabCategory.IAB23_6},
        {name: 'Islam (IAB23-7)', value: APP_CONSTANTS.iabCategory.IAB23_7},
        {name: 'Judaism (IAB23-8)', value: APP_CONSTANTS.iabCategory.IAB23_8},
        {
            name: 'Latter-Day Saints (IAB23-9)',
            value: APP_CONSTANTS.iabCategory.IAB23_9,
        },
        {
            name: 'Pagan/Wiccan (IAB23-10)',
            value: APP_CONSTANTS.iabCategory.IAB23_10,
        },
        {
            name: 'Unmoderated UGC (IAB25-1)',
            value: APP_CONSTANTS.iabCategory.IAB25_1,
        },
        {
            name: 'Extreme Graphic/Explicit Violence (IAB25-2)',
            value: APP_CONSTANTS.iabCategory.IAB25_2,
        },
        {
            name: 'Pornography (IAB25-3)',
            value: APP_CONSTANTS.iabCategory.IAB25_3,
        },
        {
            name: 'Profane Content (IAB25-4)',
            value: APP_CONSTANTS.iabCategory.IAB25_4,
        },
        {
            name: 'Hate Content (IAB25-5)',
            value: APP_CONSTANTS.iabCategory.IAB25_5,
        },
        {
            name: 'Under Construction (IAB25-6)',
            value: APP_CONSTANTS.iabCategory.IAB25_6,
        },
        {
            name: 'Incentivized (IAB25-7)',
            value: APP_CONSTANTS.iabCategory.IAB25_7,
        },
        {
            name: 'Illegal Content (IAB26-1)',
            value: APP_CONSTANTS.iabCategory.IAB26_1,
        },
        {name: 'Warez (IAB26-2)', value: APP_CONSTANTS.iabCategory.IAB26_2},
        {
            name: 'Spyware/Malware (IAB26-3)',
            value: APP_CONSTANTS.iabCategory.IAB26_3,
        },
        {
            name: 'CopyrightInfringement (IAB26-4)',
            value: APP_CONSTANTS.iabCategory.IAB26_4,
        },
    ],
    legacyIabCategories: [
        {
            name: 'Uncategorized (IAB24)',
            value: APP_CONSTANTS.legacyIabCategory.IAB24,
        },
        {
            name: 'Books & Literature (IAB1-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB1_1,
        },
        {
            name: 'Celebrity Fan/Gossip (IAB1-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB1_2,
        },
        {
            name: 'Fine Art (IAB1-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB1_3,
        },
        {name: 'Humor (IAB1-4)', value: APP_CONSTANTS.legacyIabCategory.IAB1_4},
        {
            name: 'Movies (IAB1-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB1_5,
        },
        {name: 'Music (IAB1-6)', value: APP_CONSTANTS.legacyIabCategory.IAB1_6},
        {
            name: 'Television (IAB1-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB1_7,
        },
        {
            name: 'Auto Parts (IAB2-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_1,
        },
        {
            name: 'Auto Repair (IAB2-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_2,
        },
        {
            name: 'Buying/Selling Cars (IAB2-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_3,
        },
        {
            name: 'Car Culture (IAB2-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_4,
        },
        {
            name: 'Certified Pre-Owned (IAB2-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_5,
        },
        {
            name: 'Convertible (IAB2-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_6,
        },
        {name: 'Coupe (IAB2-7)', value: APP_CONSTANTS.legacyIabCategory.IAB2_7},
        {
            name: 'Crossover (IAB2-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_8,
        },
        {
            name: 'Diesel (IAB2-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_9,
        },
        {
            name: 'Electric Vehicle (IAB2-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_10,
        },
        {
            name: 'Hatchback (IAB2-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_11,
        },
        {
            name: 'Hybrid (IAB2-12)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_12,
        },
        {
            name: 'Luxury (IAB2-13)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_13,
        },
        {
            name: 'MiniVan (IAB2-14)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_14,
        },
        {
            name: 'Mororcycles (IAB2-15)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_15,
        },
        {
            name: 'Off-Road Vehicles (IAB2-16)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_16,
        },
        {
            name: 'Performance Vehicles (IAB2-17)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_17,
        },
        {
            name: 'Pickup (IAB2-18)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_18,
        },
        {
            name: 'Road-Side Assistance (IAB2-19)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_19,
        },
        {
            name: 'Sedan (IAB2-20)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_20,
        },
        {
            name: 'Trucks & Accessories (IAB2-21)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_21,
        },
        {
            name: 'Vintage Cars (IAB2-22)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_22,
        },
        {
            name: 'Wagon (IAB2-23)',
            value: APP_CONSTANTS.legacyIabCategory.IAB2_23,
        },
        {
            name: 'Advertising (IAB3-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_1,
        },
        {
            name: 'Agriculture (IAB3-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_2,
        },
        {
            name: 'Biotech/Biomedical (IAB3-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_3,
        },
        {
            name: 'Business Software (IAB3-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_4,
        },
        {
            name: 'Construction (IAB3-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_5,
        },
        {
            name: 'Forestry (IAB3-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_6,
        },
        {
            name: 'Government (IAB3-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_7,
        },
        {
            name: 'Green Solutions (IAB3-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_8,
        },
        {
            name: 'Human Resources (IAB3-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_9,
        },
        {
            name: 'Logistics (IAB3-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_10,
        },
        {
            name: 'Marketing (IAB3-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_11,
        },
        {
            name: 'Metals (IAB3-12)',
            value: APP_CONSTANTS.legacyIabCategory.IAB3_12,
        },
        {
            name: 'Career Planning (IAB4-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_1,
        },
        {
            name: 'College (IAB4-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_2,
        },
        {
            name: 'Financial Aid (IAB4-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_3,
        },
        {
            name: 'Job Fairs (IAB4-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_4,
        },
        {
            name: 'Job Search (IAB4-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_5,
        },
        {
            name: 'Resume Writing/Advice (IAB4-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_6,
        },
        {
            name: 'Nursing (IAB4-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_7,
        },
        {
            name: 'Scholarships (IAB4-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_8,
        },
        {
            name: 'Telecommuting (IAB4-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_9,
        },
        {
            name: 'U.S. Military (IAB4-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_10,
        },
        {
            name: 'Career Advice (IAB4-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB4_11,
        },
        {
            name: '7-12 Education (IAB5-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_1,
        },
        {
            name: 'Adult Education (IAB5-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_2,
        },
        {
            name: 'Art History (IAB5-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_3,
        },
        {
            name: 'Colledge Administration (IAB5-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_4,
        },
        {
            name: 'College Life (IAB5-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_5,
        },
        {
            name: 'Distance Learning (IAB5-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_6,
        },
        {
            name: 'English as a 2nd Language (IAB5-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_7,
        },
        {
            name: 'Language Learning (IAB5-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_8,
        },
        {
            name: 'Graduate School (IAB5-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_9,
        },
        {
            name: 'Homeschooling (IAB5-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_10,
        },
        {
            name: 'Homework/Study Tips (IAB5-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_11,
        },
        {
            name: 'K-6 Educators (IAB5-12)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_12,
        },
        {
            name: 'Private School (IAB5-13)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_13,
        },
        {
            name: 'Special Education (IAB5-14)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_14,
        },
        {
            name: 'Studying Business (IAB5-15)',
            value: APP_CONSTANTS.legacyIabCategory.IAB5_15,
        },
        {
            name: 'Adoption (IAB6-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB6_1,
        },
        {
            name: 'Babies & Toddlers (IAB6-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB6_2,
        },
        {
            name: 'Daycare/Pre School (IAB6-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB6_3,
        },
        {
            name: 'Family Internet (IAB6-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB6_4,
        },
        {
            name: 'Parenting - K-6 Kids (IAB6-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB6_5,
        },
        {
            name: 'Parenting teens (IAB6-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB6_6,
        },
        {
            name: 'Pregnancy (IAB6-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB6_7,
        },
        {
            name: 'Special Needs Kids (IAB6-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB6_8,
        },
        {
            name: 'Eldercare (IAB6-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB6_9,
        },
        {
            name: 'Exercise (IAB7-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_1,
        },
        {
            name: 'A.D.D. (IAB7-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_2,
        },
        {
            name: 'AIDS/HIV (IAB7-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_3,
        },
        {
            name: 'Allergies (IAB7-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_4,
        },
        {
            name: 'Alternative Medicine (IAB7-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_5,
        },
        {
            name: 'Arthritis (IAB7-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_6,
        },
        {
            name: 'Asthma (IAB7-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_7,
        },
        {
            name: 'Autism/PDD (IAB7-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_8,
        },
        {
            name: 'Bipolar Disorder (IAB7-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_9,
        },
        {
            name: 'Brain Tumor (IAB7-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_10,
        },
        {
            name: 'Cancer (IAB7-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_11,
        },
        {
            name: 'Cholesterol (IAB7-12)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_12,
        },
        {
            name: 'Chronic Fatigue Syndrome (IAB7-13)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_13,
        },
        {
            name: 'Chronic Pain (IAB7-14)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_14,
        },
        {
            name: 'Cold & Flu (IAB7-15)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_15,
        },
        {
            name: 'Deafness (IAB7-16)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_16,
        },
        {
            name: 'Dental Care (IAB7-17)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_17,
        },
        {
            name: 'Depression (IAB7-18)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_18,
        },
        {
            name: 'Dermatology (IAB7-19)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_19,
        },
        {
            name: 'Diabetes (IAB7-20)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_20,
        },
        {
            name: 'Epilepsy (IAB7-21)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_21,
        },
        {
            name: 'GERD/Acid Reflux (IAB7-22)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_22,
        },
        {
            name: 'Headaches/Migraines (IAB7-23)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_23,
        },
        {
            name: 'Heart Disease (IAB7-24)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_24,
        },
        {
            name: 'Herbs for Health (IAB7-25)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_25,
        },
        {
            name: 'Holistic Healing (IAB7-26)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_26,
        },
        {
            name: "IBS/Crohn's Disease (IAB7-27)",
            value: APP_CONSTANTS.legacyIabCategory.IAB7_27,
        },
        {
            name: 'Incest/Abuse Support (IAB7-28)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_28,
        },
        {
            name: 'Incontinence (IAB7-29)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_29,
        },
        {
            name: 'Infertility (IAB7-30)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_30,
        },
        {
            name: "Men's Health (IAB7-31)",
            value: APP_CONSTANTS.legacyIabCategory.IAB7_31,
        },
        {
            name: 'Nutrition (IAB7-32)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_32,
        },
        {
            name: 'Orthopedics (IAB7-33)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_33,
        },
        {
            name: 'Panic/Anxiety Disorders (IAB7-34)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_34,
        },
        {
            name: 'Pediatrics (IAB7-35)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_35,
        },
        {
            name: 'Physical Therapy (IAB7-36)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_36,
        },
        {
            name: 'Psychology/Psychiatry (IAB7-37)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_37,
        },
        {
            name: 'Senior Health (IAB7-38)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_38,
        },
        {
            name: 'Sexuality (IAB7-39)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_39,
        },
        {
            name: 'Sleep Disorders (IAB7-40)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_40,
        },
        {
            name: 'Smoking Cessation (IAB7-41)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_41,
        },
        {
            name: 'Substance Abuse (IAB7-42)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_42,
        },
        {
            name: 'Thyroid Disease (IAB7-43)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_43,
        },
        {
            name: 'Weight Loss (IAB7-44)',
            value: APP_CONSTANTS.legacyIabCategory.IAB7_44,
        },
        {
            name: "Women's Health (IAB7-45)",
            value: APP_CONSTANTS.legacyIabCategory.IAB7_45,
        },
        {
            name: 'American Cuisine (IAB8-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_1,
        },
        {
            name: 'Barbecues & Grilling (IAB8-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_2,
        },
        {
            name: 'Cajun/Creole (IAB8-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_3,
        },
        {
            name: 'Chinese Cuisine (IAB8-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_4,
        },
        {
            name: 'Cocktails/Beer (IAB8-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_5,
        },
        {
            name: 'Coffee/Tea (IAB8-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_6,
        },
        {
            name: 'Cuisine-Specific (IAB8-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_7,
        },
        {
            name: 'Desserts & Baking (IAB8-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_8,
        },
        {
            name: 'Dining Out (IAB8-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_9,
        },
        {
            name: 'Food Allergies (IAB8-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_10,
        },
        {
            name: 'French Cuisine (IAB8-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_11,
        },
        {
            name: 'Health/Lowfat Cooking (IAB8-12)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_12,
        },
        {
            name: 'Italian Cuisine (IAB8-13)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_13,
        },
        {
            name: 'Japanese Cuisine (IAB8-14)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_14,
        },
        {
            name: 'Mexican Cuisine (IAB8-15)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_15,
        },
        {
            name: 'Vegan (IAB8-16)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_16,
        },
        {
            name: 'Vegetarian (IAB8-17)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_17,
        },
        {
            name: 'Wine (IAB8-18)',
            value: APP_CONSTANTS.legacyIabCategory.IAB8_18,
        },
        {
            name: 'Art/Technology (IAB9-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_1,
        },
        {
            name: 'Arts & Crafts (IAB9-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_2,
        },
        {
            name: 'Beadwork (IAB9-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_3,
        },
        {
            name: 'Birdwatching (IAB9-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_4,
        },
        {
            name: 'Board Games/Puzzles (IAB9-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_5,
        },
        {
            name: 'Candle & Soap Making (IAB9-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_6,
        },
        {
            name: 'Card Games (IAB9-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_7,
        },
        {name: 'Chess (IAB9-8)', value: APP_CONSTANTS.legacyIabCategory.IAB9_8},
        {
            name: 'Cigars (IAB9-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_9,
        },
        {
            name: 'Collecting (IAB9-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_10,
        },
        {
            name: 'Comic Books (IAB9-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_11,
        },
        {
            name: 'Drawing/Sketching (IAB9-12)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_12,
        },
        {
            name: 'Freelance Writing (IAB9-13)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_13,
        },
        {
            name: 'Genealogy (IAB9-14)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_14,
        },
        {
            name: 'Getting Published (IAB9-15)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_15,
        },
        {
            name: 'Guitar (IAB9-16)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_16,
        },
        {
            name: 'Home Recording (IAB9-17)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_17,
        },
        {
            name: 'Investors & Patents (IAB9-18)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_18,
        },
        {
            name: 'Jewelry Making (IAB9-19)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_19,
        },
        {
            name: 'Magic & Illusion (IAB9-20)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_20,
        },
        {
            name: 'Needlework (IAB9-21)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_21,
        },
        {
            name: 'Painting (IAB9-22)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_22,
        },
        {
            name: 'Photography (IAB9-23)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_23,
        },
        {
            name: 'Radio (IAB9-24)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_24,
        },
        {
            name: 'Roleplaying Games (IAB9-25)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_25,
        },
        {
            name: 'Sci-Fi & Fantasy (IAB9-26)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_26,
        },
        {
            name: 'Scrapbooking (IAB9-27)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_27,
        },
        {
            name: 'Screenwriting (IAB9-28)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_28,
        },
        {
            name: 'Stamps & Coins (IAB9-29)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_29,
        },
        {
            name: 'Video & Computer Games (IAB9-30)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_30,
        },
        {
            name: 'Woodworking (IAB9-31)',
            value: APP_CONSTANTS.legacyIabCategory.IAB9_31,
        },
        {
            name: 'Appliances (IAB10-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB10_1,
        },
        {
            name: 'Entertaining (IAB10-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB10_2,
        },
        {
            name: 'Environmental Safety (IAB10-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB10_3,
        },
        {
            name: 'Gardening (IAB10-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB10_4,
        },
        {
            name: 'Home Repair (IAB10-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB10_5,
        },
        {
            name: 'Home Theater (IAB10-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB10_6,
        },
        {
            name: 'Interior Decorating (IAB10-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB10_7,
        },
        {
            name: 'Landscaping (IAB10-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB10_8,
        },
        {
            name: 'Remodeling & Construction (IAB10-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB10_9,
        },
        {
            name: 'Immigration (IAB11-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB11_1,
        },
        {
            name: 'Legal Issues (IAB11-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB11_2,
        },
        {
            name: 'U.S. Government Resources (IAB11-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB11_3,
        },
        {
            name: 'Politics (IAB11-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB11_4,
        },
        {
            name: 'Commentary (IAB11-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB11_5,
        },
        {
            name: 'International News (IAB12-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB12_1,
        },
        {
            name: 'National News (IAB12-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB12_2,
        },
        {
            name: 'Local News (IAB12-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB12_3,
        },
        {
            name: 'Beginning Investing (IAB13-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_1,
        },
        {
            name: 'Credit/Debt & Loans (IAB13-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_2,
        },
        {
            name: 'Financial News (IAB13-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_3,
        },
        {
            name: 'Financial Planning (IAB13-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_4,
        },
        {
            name: 'Hedge Fund (IAB13-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_5,
        },
        {
            name: 'Insurance (IAB13-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_6,
        },
        {
            name: 'Investing (IAB13-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_7,
        },
        {
            name: 'Mutual Funds (IAB13-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_8,
        },
        {
            name: 'Options (IAB13-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_9,
        },
        {
            name: 'Retirement Planning (IAB13-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_10,
        },
        {
            name: 'Stocks (IAB13-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_11,
        },
        {
            name: 'Tax Planning (IAB13-12)',
            value: APP_CONSTANTS.legacyIabCategory.IAB13_12,
        },
        {
            name: 'Dating (IAB14-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB14_1,
        },
        {
            name: 'Divorce Support (IAB14-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB14_2,
        },
        {
            name: 'Gay Life (IAB14-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB14_3,
        },
        {
            name: 'Marriage (IAB14-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB14_4,
        },
        {
            name: 'Senior Living (IAB14-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB14_5,
        },
        {
            name: 'Teens (IAB14-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB14_6,
        },
        {
            name: 'Weddings (IAB14-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB14_7,
        },
        {
            name: 'Ethnic Specific (IAB14-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB14_8,
        },
        {
            name: 'Astrology (IAB15-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB15_1,
        },
        {
            name: 'Biology (IAB15-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB15_2,
        },
        {
            name: 'Chemistry (IAB15-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB15_3,
        },
        {
            name: 'Geology (IAB15-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB15_4,
        },
        {
            name: 'Paranormal Phenomena (IAB15-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB15_5,
        },
        {
            name: 'Physics (IAB15-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB15_6,
        },
        {
            name: 'Space/Astronomy (IAB15-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB15_7,
        },
        {
            name: 'Geography (IAB15-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB15_8,
        },
        {
            name: 'Botany (IAB15-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB15_9,
        },
        {
            name: 'Weather (IAB15-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB15_10,
        },
        {
            name: 'Aquariums (IAB16-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB16_1,
        },
        {
            name: 'Birds (IAB16-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB16_2,
        },
        {
            name: 'Cats (IAB16-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB16_3,
        },
        {
            name: 'Dogs (IAB16-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB16_4,
        },
        {
            name: 'Large Animals (IAB16-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB16_5,
        },
        {
            name: 'Reptiles (IAB16-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB16_6,
        },
        {
            name: 'Veterinary Medicine (IAB16-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB16_7,
        },
        {
            name: 'Auto Racing (IAB17-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_1,
        },
        {
            name: 'Baseball (IAB17-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_2,
        },
        {
            name: 'Bicycling (IAB17-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_3,
        },
        {
            name: 'Bodybuilding (IAB17-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_4,
        },
        {
            name: 'Boxing (IAB17-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_5,
        },
        {
            name: 'Canoeing/Kayaking (IAB17-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_6,
        },
        {
            name: 'Cheerleading (IAB17-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_7,
        },
        {
            name: 'Climbing (IAB17-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_8,
        },
        {
            name: 'Cricket (IAB17-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_9,
        },
        {
            name: 'Figure Skating (IAB17-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_10,
        },
        {
            name: 'Fly Fishing (IAB17-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_11,
        },
        {
            name: 'Football (IAB17-12)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_12,
        },
        {
            name: 'Freshwater Fishing (IAB17-13)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_13,
        },
        {
            name: 'Game & Fish (IAB17-14)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_14,
        },
        {
            name: 'Golf (IAB17-15)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_15,
        },
        {
            name: 'Horse Racing (IAB17-16)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_16,
        },
        {
            name: 'Horses (IAB17-17)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_17,
        },
        {
            name: 'Hunting/Shooting (IAB17-18)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_18,
        },
        {
            name: 'Inline Skating (IAB17-19)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_19,
        },
        {
            name: 'Martial Arts (IAB17-20)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_20,
        },
        {
            name: 'Mountain Biking (IAB17-21)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_21,
        },
        {
            name: 'NASCAR Racing (IAB17-22)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_22,
        },
        {
            name: 'Olympics (IAB17-23)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_23,
        },
        {
            name: 'Paintball (IAB17-24)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_24,
        },
        {
            name: 'Power & Motorcycles (IAB17-25)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_25,
        },
        {
            name: 'Pro Basketball (IAB17-26)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_26,
        },
        {
            name: 'Pro Ice Hockey (IAB17-27)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_27,
        },
        {
            name: 'Rodeo (IAB17-28)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_28,
        },
        {
            name: 'Rugby (IAB17-29)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_29,
        },
        {
            name: 'Running/Jogging (IAB17-30)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_30,
        },
        {
            name: 'Sailing (IAB17-31)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_31,
        },
        {
            name: 'Saltwater Fishing (IAB17-32)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_32,
        },
        {
            name: 'Scuba Diving (IAB17-33)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_33,
        },
        {
            name: 'Skateboarding (IAB17-34)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_34,
        },
        {
            name: 'Skiing (IAB17-35)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_35,
        },
        {
            name: 'Snowboarding (IAB17-36)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_36,
        },
        {
            name: 'Surfing/Bodyboarding (IAB17-37)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_37,
        },
        {
            name: 'Swimming (IAB17-38)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_38,
        },
        {
            name: 'Table Tennis/Ping-Pong (IAB17-39)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_39,
        },
        {
            name: 'Tennis (IAB17-40)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_40,
        },
        {
            name: 'Volleyball (IAB17-41)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_41,
        },
        {
            name: 'Walking (IAB17-42)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_42,
        },
        {
            name: 'Waterski/Wakeboard (IAB17-43)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_43,
        },
        {
            name: 'World Soccer (IAB17-44)',
            value: APP_CONSTANTS.legacyIabCategory.IAB17_44,
        },
        {
            name: 'Beauty (IAB18-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB18_1,
        },
        {
            name: 'Body Art (IAB18-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB18_2,
        },
        {
            name: 'Fashion (IAB18-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB18_3,
        },
        {
            name: 'Jewelry (IAB18-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB18_4,
        },
        {
            name: 'Clothing (IAB18-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB18_5,
        },
        {
            name: 'Accessories (IAB18-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB18_6,
        },
        {
            name: '3-D Graphics (IAB19-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_1,
        },
        {
            name: 'Animation (IAB19-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_2,
        },
        {
            name: 'Antivirus Software (IAB19-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_3,
        },
        {
            name: 'C/C++ (IAB19-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_4,
        },
        {
            name: 'Cameras & Camcorders (IAB19-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_5,
        },
        {
            name: 'Cell Phones (IAB19-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_6,
        },
        {
            name: 'Computer Certification (IAB19-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_7,
        },
        {
            name: 'Computer Networking (IAB19-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_8,
        },
        {
            name: 'Computer Peripherals (IAB19-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_9,
        },
        {
            name: 'Computer Reviews (IAB19-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_10,
        },
        {
            name: 'Data Centers (IAB19-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_11,
        },
        {
            name: 'Databases (IAB19-12)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_12,
        },
        {
            name: 'Desktop Publishing (IAB19-13)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_13,
        },
        {
            name: 'Desktop Video (IAB19-14)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_14,
        },
        {
            name: 'Email (IAB19-15)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_15,
        },
        {
            name: 'Graphics Software (IAB19-16)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_16,
        },
        {
            name: 'Home Video/DVD (IAB19-17)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_17,
        },
        {
            name: 'Internet Technology (IAB19-18)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_18,
        },
        {
            name: 'Java (IAB19-19)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_19,
        },
        {
            name: 'JavaScript (IAB19-20)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_20,
        },
        {
            name: 'Mac Support (IAB19-21)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_21,
        },
        {
            name: 'MP3/MIDI (IAB19-22)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_22,
        },
        {
            name: 'Net Conferencing (IAB19-23)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_23,
        },
        {
            name: 'Net for Beginners (IAB19-24)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_24,
        },
        {
            name: 'Network Security (IAB19-25)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_25,
        },
        {
            name: 'Palmtops/PDAs (IAB19-26)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_26,
        },
        {
            name: 'PC Support (IAB19-27)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_27,
        },
        {
            name: 'Portable (IAB19-28)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_28,
        },
        {
            name: 'Entertainment (IAB19-29)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_29,
        },
        {
            name: 'Shareware/Freeware (IAB19-30)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_30,
        },
        {
            name: 'Unix (IAB19-31)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_31,
        },
        {
            name: 'Visual Basic (IAB19-32)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_32,
        },
        {
            name: 'Web Clip Art (IAB19-33)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_33,
        },
        {
            name: 'Web Design/HTML (IAB19-34)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_34,
        },
        {
            name: 'Web Search (IAB19-35)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_35,
        },
        {
            name: 'Windows (IAB19-36)',
            value: APP_CONSTANTS.legacyIabCategory.IAB19_36,
        },
        {
            name: 'Adventure Travel (IAB20-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_1,
        },
        {
            name: 'Africa (IAB20-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_2,
        },
        {
            name: 'Air Travel (IAB20-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_3,
        },
        {
            name: 'Australia & New Zealand (IAB20-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_4,
        },
        {
            name: 'Bed & Breakfasts (IAB20-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_5,
        },
        {
            name: 'Budget Travel (IAB20-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_6,
        },
        {
            name: 'Business Travel (IAB20-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_7,
        },
        {
            name: 'By US Locale (IAB20-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_8,
        },
        {
            name: 'Camping (IAB20-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_9,
        },
        {
            name: 'Canada (IAB20-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_10,
        },
        {
            name: 'Caribbean (IAB20-11)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_11,
        },
        {
            name: 'Cruises (IAB20-12)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_12,
        },
        {
            name: 'Eastern Europe (IAB20-13)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_13,
        },
        {
            name: 'Europe (IAB20-14)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_14,
        },
        {
            name: 'France (IAB20-15)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_15,
        },
        {
            name: 'Greece (IAB20-16)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_16,
        },
        {
            name: 'Honeymoons/Getaways (IAB20-17)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_17,
        },
        {
            name: 'Hotels (IAB20-18)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_18,
        },
        {
            name: 'Italy (IAB20-19)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_19,
        },
        {
            name: 'Japan (IAB20-20)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_20,
        },
        {
            name: 'Mexico & Central America (IAB20-21)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_21,
        },
        {
            name: 'National Parks (IAB20-22)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_22,
        },
        {
            name: 'South America (IAB20-23)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_23,
        },
        {
            name: 'Spas (IAB20-24)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_24,
        },
        {
            name: 'Theme Parks (IAB20-25)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_25,
        },
        {
            name: 'Traveling with Kids (IAB20-26)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_26,
        },
        {
            name: 'United Kingdom (IAB20-27)',
            value: APP_CONSTANTS.legacyIabCategory.IAB20_27,
        },
        {
            name: 'Apartments (IAB21-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB21_1,
        },
        {
            name: 'Architects (IAB21-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB21_2,
        },
        {
            name: 'Buying/Selling Homes (IAB21-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB21_3,
        },
        {
            name: 'Contests & Freebies (IAB22-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB22_1,
        },
        {
            name: 'Couponing (IAB22-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB22_2,
        },
        {
            name: 'Comparison (IAB22-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB22_3,
        },
        {
            name: 'Engines (IAB22-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB22_4,
        },
        {
            name: 'Alternative Religions (IAB23-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB23_1,
        },
        {
            name: 'Atheism/Agnosticism (IAB23-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB23_2,
        },
        {
            name: 'Buddhism (IAB23-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB23_3,
        },
        {
            name: 'Catholicism (IAB23-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB23_4,
        },
        {
            name: 'Christianity (IAB23-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB23_5,
        },
        {
            name: 'Hinduism (IAB23-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB23_6,
        },
        {
            name: 'Islam (IAB23-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB23_7,
        },
        {
            name: 'Judaism (IAB23-8)',
            value: APP_CONSTANTS.legacyIabCategory.IAB23_8,
        },
        {
            name: 'Latter-Day Saints (IAB23-9)',
            value: APP_CONSTANTS.legacyIabCategory.IAB23_9,
        },
        {
            name: 'Pagan/Wiccan (IAB23-10)',
            value: APP_CONSTANTS.legacyIabCategory.IAB23_10,
        },
        {
            name: 'Unmoderated UGC (IAB25-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB25_1,
        },
        {
            name: 'Extreme Graphic/Explicit Violence (IAB25-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB25_2,
        },
        {
            name: 'Pornography (IAB25-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB25_3,
        },
        {
            name: 'Profane Content (IAB25-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB25_4,
        },
        {
            name: 'Hate Content (IAB25-5)',
            value: APP_CONSTANTS.legacyIabCategory.IAB25_5,
        },
        {
            name: 'Under Construction (IAB25-6)',
            value: APP_CONSTANTS.legacyIabCategory.IAB25_6,
        },
        {
            name: 'Incentivized (IAB25-7)',
            value: APP_CONSTANTS.legacyIabCategory.IAB25_7,
        },
        {
            name: 'Illegal Content (IAB26-1)',
            value: APP_CONSTANTS.legacyIabCategory.IAB26_1,
        },
        {
            name: 'Warez (IAB26-2)',
            value: APP_CONSTANTS.legacyIabCategory.IAB26_2,
        },
        {
            name: 'Spyware/Malware (IAB26-3)',
            value: APP_CONSTANTS.legacyIabCategory.IAB26_3,
        },
        {
            name: 'CopyrightInfringement (IAB26-4)',
            value: APP_CONSTANTS.legacyIabCategory.IAB26_4,
        },
    ],
    promotionGoals: [
        {
            name: 'Brand Building',
            value: APP_CONSTANTS.promotionGoal.BRAND_BUILDING,
        },
        {
            name: 'Traffic Acquisition',
            value: APP_CONSTANTS.promotionGoal.TRAFFIC_ACQUISITION,
        },
        {name: 'Conversions', value: APP_CONSTANTS.promotionGoal.CONVERSIONS},
    ],
    campaignGoals: [
        {name: 'CPA', value: APP_CONSTANTS.campaignGoal.CPA},
        {
            name: '% bounce rate',
            value: APP_CONSTANTS.campaignGoal.PERCENT_BOUNCE_RATE,
        },
        {
            name: 'new users',
            value: APP_CONSTANTS.campaignGoal.NEW_UNIQUE_VISITORS,
        },
        {
            name: 'seconds time on site',
            value: APP_CONSTANTS.campaignGoal.SECONDS_TIME_ON_SITE,
        },
        {
            name: 'pages per session',
            value: APP_CONSTANTS.campaignGoal.PAGES_PER_SESSION,
        },
    ],
    campaignGoalKPIs: [
        {
            name: 'Time on Site - Seconds',
            value: APP_CONSTANTS.campaignGoalKPI.TIME_ON_SITE,
            unit: 's',
        },
        {
            name: 'Max Bounce Rate',
            value: APP_CONSTANTS.campaignGoalKPI.MAX_BOUNCE_RATE,
            unit: '%',
        },
        {
            name: 'Pageviews per Visit',
            value: APP_CONSTANTS.campaignGoalKPI.PAGES_PER_SESSION,
        },
        {
            name: 'Cost per Visit',
            value: APP_CONSTANTS.campaignGoalKPI.CPV,
            isCurrency: true,
        },
        {
            name: 'CPC',
            value: APP_CONSTANTS.campaignGoalKPI.CPC,
            isCurrency: true,
        },
        {
            name: 'New Users',
            value: APP_CONSTANTS.campaignGoalKPI.NEW_UNIQUE_VISITORS,
            unit: '%',
        },
        {
            name: 'CPA - Setup Conversion Tracking',
            value: APP_CONSTANTS.campaignGoalKPI.CPA,
            isCurrency: true,
        },
        {
            name: 'Cost per Non-Bounced Visit',
            value: APP_CONSTANTS.campaignGoalKPI.CP_NON_BOUNCED_VISIT,
            isCurrency: true,
        }, // eslint-disable-line max-len
        {
            name: 'Cost per New Visitor',
            value: APP_CONSTANTS.campaignGoalKPI.CP_NEW_VISITOR,
            isCurrency: true,
        },
        {
            name: 'Cost per Pageview',
            value: APP_CONSTANTS.campaignGoalKPI.CP_PAGE_VIEW,
            isCurrency: true,
        },
        {
            name: 'Cost per Completed Video View',
            value: APP_CONSTANTS.campaignGoalKPI.CPCV,
            isCurrency: true,
        },
    ],
    budgetAutomationGoals: [
        {
            name: 'time on site',
            value: APP_CONSTANTS.campaignGoalKPI.TIME_ON_SITE,
        },
        {
            name: 'bounce rate',
            value: APP_CONSTANTS.campaignGoalKPI.MAX_BOUNCE_RATE,
        },
        {
            name: 'pages per session',
            value: APP_CONSTANTS.campaignGoalKPI.PAGES_PER_SESSION,
        },
        {name: 'cost per visit', value: APP_CONSTANTS.campaignGoalKPI.CPV},
        {name: 'average CPC', value: APP_CONSTANTS.campaignGoalKPI.CPC},
        {
            name: 'new users',
            value: APP_CONSTANTS.campaignGoalKPI.NEW_UNIQUE_VISITORS,
        },
        {name: 'CPA', value: APP_CONSTANTS.campaignGoalKPI.CPA},
        {
            name: 'cost per non-bounced visit',
            value: APP_CONSTANTS.campaignGoalKPI.CP_NON_BOUNCED_VISIT,
        },
        {
            name: 'cost per new visitor',
            value: APP_CONSTANTS.campaignGoalKPI.CP_NEW_VISITOR,
        },
        {
            name: 'cost per pageview',
            value: APP_CONSTANTS.campaignGoalKPI.CP_PAGE_VIEW,
        },
        {
            name: 'cost per completed video view',
            value: APP_CONSTANTS.campaignGoalKPI.CPCV,
        },
    ],
    conversionGoalTypes: [
        {name: 'Pixel', value: APP_CONSTANTS.conversionGoalType.PIXEL},
        {name: 'Google Analytics', value: APP_CONSTANTS.conversionGoalType.GA},
        {
            name: 'Adobe Analytics',
            value: APP_CONSTANTS.conversionGoalType.OMNITURE,
        },
    ],
    conversionWindows: [
        {name: '1 day', value: APP_CONSTANTS.conversionWindow.LEQ_1_DAY},
        {name: '7 days', value: APP_CONSTANTS.conversionWindow.LEQ_7_DAYS},
        {name: '30 days', value: APP_CONSTANTS.conversionWindow.LEQ_30_DAYS},
    ],
    conversionWindowsLegacy: [
        {name: '1 day', value: APP_CONSTANTS.conversionWindow.LEQ_1_DAY},
        {name: '7 days', value: APP_CONSTANTS.conversionWindow.LEQ_7_DAYS},
        {name: '30 days', value: APP_CONSTANTS.conversionWindow.LEQ_30_DAYS},
        {name: '90 days', value: APP_CONSTANTS.conversionWindow.LEQ_90_DAYS},
    ],
    conversionWindowsViewthrough: [
        {name: '1 day', value: APP_CONSTANTS.conversionWindow.LEQ_1_DAY},
    ],
    exportFrequency: [
        {name: 'Daily', value: APP_CONSTANTS.exportFrequency.DAILY},
        {name: 'Weekly', value: APP_CONSTANTS.exportFrequency.WEEKLY},
        {name: 'Monthly (1st)', value: APP_CONSTANTS.exportFrequency.MONTHLY},
    ],
    exportDayOfWeek: [
        {name: 'Sunday', value: APP_CONSTANTS.exportDayOfWeek.SUNDAY},
        {name: 'Monday', value: APP_CONSTANTS.exportDayOfWeek.MONDAY},
        {name: 'Tuesday', value: APP_CONSTANTS.exportDayOfWeek.TUESDAY},
        {name: 'Wednesday', value: APP_CONSTANTS.exportDayOfWeek.WEDNESDAY},
        {name: 'Thursday', value: APP_CONSTANTS.exportDayOfWeek.THURSDAY},
        {name: 'Friday', value: APP_CONSTANTS.exportDayOfWeek.FRIDAY},
        {name: 'Saturday', value: APP_CONSTANTS.exportDayOfWeek.SATURDAY},
    ],
    exportTimePeriod: [
        {name: 'Yesterday', value: APP_CONSTANTS.exportTimePeriod.YESTERDAY},
        {
            name: 'Last 7 Days',
            value: APP_CONSTANTS.exportTimePeriod.LAST_7_DAYS,
        },
        {
            name: 'Last 30 Days',
            value: APP_CONSTANTS.exportTimePeriod.LAST_30_DAYS,
        },
        {name: 'This Week', value: APP_CONSTANTS.exportTimePeriod.THIS_WEEK},
        {name: 'Last Week', value: APP_CONSTANTS.exportTimePeriod.LAST_WEEK},
        {name: 'This Month', value: APP_CONSTANTS.exportTimePeriod.THIS_MONTH},
        {name: 'Last Month', value: APP_CONSTANTS.exportTimePeriod.LAST_MONTH},
    ],
    imageCrops: [
        {name: 'Center', value: APP_CONSTANTS.imageCrop.CENTER},
        {name: 'Faces', value: APP_CONSTANTS.imageCrop.FACES},
        {name: 'Entropy', value: APP_CONSTANTS.imageCrop.ENTROPY},
        {name: 'Left', value: APP_CONSTANTS.imageCrop.LEFT},
        {name: 'Right', value: APP_CONSTANTS.imageCrop.RIGHT},
        {name: 'Top', value: APP_CONSTANTS.imageCrop.TOP},
        {name: 'Bottom', value: APP_CONSTANTS.imageCrop.BOTTOM},
    ],
    videoTypes: [
        {name: 'Video file', value: APP_CONSTANTS.videoType.DIRECT_UPLOAD},
        {name: 'VAST XML file', value: APP_CONSTANTS.videoType.VAST_UPLOAD},
        {name: 'VAST tag', value: APP_CONSTANTS.videoType.VAST_URL},
    ],
    gaTrackingType: [
        {name: 'Email', value: APP_CONSTANTS.gaTrackingType.EMAIL},
        {name: 'API', value: APP_CONSTANTS.gaTrackingType.API},
    ],
    interests: [
        {
            name: 'Arts & Entertainment',
            value: APP_CONSTANTS.interestCategory.ENTERTAINMENT,
        },
        {
            name: 'Viral, lists & Quizzes',
            value: APP_CONSTANTS.interestCategory.FUN_QUIZZES,
        },
        {name: 'Music', value: APP_CONSTANTS.interestCategory.MUSIC},
        {name: 'Automotive', value: APP_CONSTANTS.interestCategory.CARS},
        {
            name: 'Business & Finance',
            value: APP_CONSTANTS.interestCategory.FINANCE,
        },
        {name: 'Education', value: APP_CONSTANTS.interestCategory.EDUCATION},
        {
            name: 'Family & Parenting',
            value: APP_CONSTANTS.interestCategory.FAMILY,
        },
        {
            name: 'Health & Fitness',
            value: APP_CONSTANTS.interestCategory.HEALTH,
        },
        {name: 'Food & Drink', value: APP_CONSTANTS.interestCategory.FOOD},
        {
            name: 'Hobbies & Interests',
            value: APP_CONSTANTS.interestCategory.HOBBIES,
        },
        {name: 'Games & Gaming', value: APP_CONSTANTS.interestCategory.GAMES},
        {name: 'Home & Garden', value: APP_CONSTANTS.interestCategory.HOME},
        {
            name: 'Law, Gov’t & Politics',
            value: APP_CONSTANTS.interestCategory.POLITICS_LAW,
        },
        {name: 'News', value: APP_CONSTANTS.interestCategory.MEDIA},
        {
            name: 'Dating & Relationships',
            value: APP_CONSTANTS.interestCategory.DATING,
        },
        {name: 'Science', value: APP_CONSTANTS.interestCategory.SCIENCE},
        {
            name: 'Weather & Environment',
            value: APP_CONSTANTS.interestCategory.WEATHER,
        },
        {name: 'Pets', value: APP_CONSTANTS.interestCategory.PETS},
        {name: 'Sports', value: APP_CONSTANTS.interestCategory.SPORTS},
        {
            name: 'Beauty & Fashion',
            value: APP_CONSTANTS.interestCategory.FASHION,
        },
        {name: 'Technology', value: APP_CONSTANTS.interestCategory.TECHNOLOGY},
        {
            name: 'Apps & Online services',
            value: APP_CONSTANTS.interestCategory.UTILITY,
        },
        {name: 'Travel', value: APP_CONSTANTS.interestCategory.TRAVEL},
        {
            name: 'Shopping',
            value: APP_CONSTANTS.interestCategory.SHOPPING_COUPONS,
        },
        {
            name: 'Religion & Spirituality',
            value: APP_CONSTANTS.interestCategory.RELIGION,
        },
        {
            name: 'Communication Tools',
            value: APP_CONSTANTS.interestCategory.COMMUNICATION,
        },
        {name: 'Careers', value: APP_CONSTANTS.interestCategory.CAREER},
        {name: 'Premium', value: APP_CONSTANTS.interestCategory.PREMIUM},
        {
            name: 'Women’s Lifestyle',
            value: APP_CONSTANTS.interestCategory.WOMEN,
        },
        {name: 'Men’s Lifestyle', value: APP_CONSTANTS.interestCategory.MEN},
        {
            name: 'Foreign',
            value: APP_CONSTANTS.interestCategory.FOREIGN,
            internal: true,
        },
        {
            name: 'French',
            value: APP_CONSTANTS.interestCategory.FRENCH,
            internal: true,
        },
        {
            name: 'Spanish',
            value: APP_CONSTANTS.interestCategory.SPANISH,
            internal: true,
        },
        {
            name: 'Other',
            value: APP_CONSTANTS.interestCategory.OTHER,
            internal: true,
        },
        {
            name: 'Unknown',
            value: APP_CONSTANTS.interestCategory.UNKNOWN,
            internal: true,
        },
        {
            name: 'Outbrain',
            value: APP_CONSTANTS.interestCategory.OUTBRAIN,
            internal: true,
        },
        {
            name: 'Technology - Contextual',
            value: APP_CONSTANTS.interestCategory.TECHNOLOGY_CONTEXTUAL,
            internal: true,
        },

        // legacy, now in combination
        {
            name: 'Fun & Entertaining Sites',
            value: APP_CONSTANTS.interestCategory.FUN,
            internal: true,
        },
        {
            name: 'Quizzes',
            value: APP_CONSTANTS.interestCategory.QUIZZES,
            internal: true,
        },
        {
            name: 'Gov’t & Politics',
            value: APP_CONSTANTS.interestCategory.POLITICS,
            internal: true,
        },
        {
            name: 'Law',
            value: APP_CONSTANTS.interestCategory.LAW,
            internal: true,
        },
        {
            name: 'Couponing',
            value: APP_CONSTANTS.interestCategory.COUPONS,
            internal: true,
        },
        {
            name: 'Shopping',
            value: APP_CONSTANTS.interestCategory.SHOPPING,
            internal: true,
        },
    ],
    adTypes: [
        {
            name: 'Content ad',
            legacyValue: APP_CONSTANTS.legacyAdType.CONTENT,
            value: APP_CONSTANTS.adType.CONTENT,
            campaignTypes: [
                APP_CONSTANTS.campaignTypes.CONTENT,
                APP_CONSTANTS.campaignTypes.CONVERSION,
                APP_CONSTANTS.campaignTypes.MOBILE,
            ],
        },
        {
            name: 'Video ad',
            legacyValue: APP_CONSTANTS.legacyAdType.VIDEO,
            value: APP_CONSTANTS.adType.VIDEO,
            campaignTypes: [APP_CONSTANTS.campaignTypes.VIDEO],
        },
        {
            name: 'Image display ad',
            legacyValue: APP_CONSTANTS.legacyAdType.IMAGE,
            value: APP_CONSTANTS.adType.IMAGE,
            campaignTypes: [APP_CONSTANTS.campaignTypes.DISPLAY],
        },
        {
            name: 'Display ad tag',
            legacyValue: APP_CONSTANTS.legacyAdType.AD_TAG,
            value: APP_CONSTANTS.adType.AD_TAG,
            campaignTypes: [APP_CONSTANTS.campaignTypes.DISPLAY],
        },
    ],
    adSizes: [
        {
            name: '320x50',
            value: APP_CONSTANTS.adSize.MOBILE_LEADERBOARD,
            width: 320,
            height: 50,
        },
        {
            name: '300x250',
            value: APP_CONSTANTS.adSize.INLINE_RECTANGLE,
            width: 300,
            height: 250,
        },
        {
            name: '728x90',
            value: APP_CONSTANTS.adSize.LEADERBOARD,
            width: 728,
            height: 90,
        },
        {
            name: '336x280',
            value: APP_CONSTANTS.adSize.LARGE_RECTANGLE,
            width: 336,
            height: 280,
        },
        {
            name: '300x600',
            value: APP_CONSTANTS.adSize.HALF_PAGE,
            width: 300,
            height: 600,
        },
        {
            name: '120x600',
            value: APP_CONSTANTS.adSize.WIDESKYSCRAPER,
            width: 120,
            height: 600,
        },
        {
            name: '320x100',
            value: APP_CONSTANTS.adSize.LARGE_MOBILE_BANNER,
            width: 320,
            height: 100,
        },
        {
            name: '468x60',
            value: APP_CONSTANTS.adSize.BANNER,
            width: 468,
            height: 60,
        },
        {
            name: '300x1050',
            value: APP_CONSTANTS.adSize.PORTRAIT,
            width: 300,
            height: 1050,
        },
        {
            name: '970x90',
            value: APP_CONSTANTS.adSize.LARGE_LEADERBOARD,
            width: 970,
            height: 90,
        },
        {
            name: '970x250',
            value: APP_CONSTANTS.adSize.BILLBOARD,
            width: 970,
            height: 250,
        },
        {
            name: '250x250',
            value: APP_CONSTANTS.adSize.SQUARE,
            width: 250,
            height: 250,
        },
        {
            name: '200x200',
            value: APP_CONSTANTS.adSize.SMALL_SQUARE,
            width: 200,
            height: 200,
        },
        {
            name: '180x150',
            value: APP_CONSTANTS.adSize.SMALL_RECTANGLE,
            width: 180,
            height: 150,
        },
        {
            name: '125x125',
            value: APP_CONSTANTS.adSize.BUTTON,
            width: 125,
            height: 125,
        },
    ],
};

// [Workaround - Webpack] Make options global
// AngularJS (backward compatibility)
(<any>window).options = APP_OPTIONS;
