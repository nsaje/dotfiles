import {
    EntityType,
    CampaignConversionGoalType,
    ConversionWindow,
    Unit,
    DataType,
    CampaignType,
    IabCategory,
    Language,
} from '../../app.constants';
import {CampaignGoalKPI, GaTrackingType} from '../../app.constants';
import {CampaignGoalKPIConfig} from './types/campaign-goal-kpi-config';
import {CampaignConversionGoalTypeConfig} from './types/campaign-conversion-goal-type-config';
import {ConversionWindowConfig} from '../../core/conversion-pixels/types/conversion-windows-config';
import {CampaignTypeConfig} from './types/campaign-type-config';
import {IabCategoryConfig} from './types/iabcategory-config';
import {LanguageConfig} from './types/language-config';

export const ENTITY_MANAGER_CONFIG = {
    settingsQueryParam: 'settings',
    idStateParam: 'id',
    levelStateParam: 'level',
    levelToEntityTypeMap: {
        account: EntityType.ACCOUNT,
        campaign: EntityType.CAMPAIGN,
        adgroup: EntityType.AD_GROUP,
    },
    maxCampaignConversionGoals: 15,
};

export const AUTOMATICALLY_OPTIMIZED_KPI_GOALS = [
    CampaignGoalKPI.MAX_BOUNCE_RATE,
    CampaignGoalKPI.NEW_UNIQUE_VISITORS,
    CampaignGoalKPI.TIME_ON_SITE,
    CampaignGoalKPI.PAGES_PER_SESSION,
    CampaignGoalKPI.CPV,
    CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
    CampaignGoalKPI.CP_NEW_VISITOR,
    CampaignGoalKPI.CP_PAGE_VIEW,
];

export const CAMPAIGN_GOAL_VALUE_TEXT = {
    [CampaignGoalKPI.MAX_BOUNCE_RATE]: '% Bounce Rate',
    [CampaignGoalKPI.NEW_UNIQUE_VISITORS]: '% New Users',
    [CampaignGoalKPI.TIME_ON_SITE]: 'seconds Time on Site',
    [CampaignGoalKPI.PAGES_PER_SESSION]: 'Pageviews per Visit',
    [CampaignGoalKPI.CPV]: 'Cost per Visit',
    [CampaignGoalKPI.CP_NON_BOUNCED_VISIT]: 'Cost per Non-Bounced Visit',
    [CampaignGoalKPI.CP_NEW_VISITOR]: 'Cost per New Visitor',
    [CampaignGoalKPI.CP_PAGE_VIEW]: 'Cost per Pageview',
    [CampaignGoalKPI.CPCV]: 'Cost per Completed Video View',
    [CampaignGoalKPI.CPA]: 'CPA',
    [CampaignGoalKPI.CPC]: 'CPC',
    [CampaignGoalKPI.CPM]: 'CPM',
};

export const CAMPAIGN_GOAL_KPIS: CampaignGoalKPIConfig[] = [
    {
        name: 'Time on Site - Seconds',
        value: CampaignGoalKPI.TIME_ON_SITE,
        dataType: DataType.Decimal,
        unit: Unit.Second,
    },
    {
        name: 'Max Bounce Rate',
        value: CampaignGoalKPI.MAX_BOUNCE_RATE,
        dataType: DataType.Decimal,
        unit: Unit.Percent,
    },
    {
        name: 'Pageviews per Visit',
        value: CampaignGoalKPI.PAGES_PER_SESSION,
        dataType: DataType.Decimal,
    },
    {
        name: 'Cost per Visit',
        value: CampaignGoalKPI.CPV,
        dataType: DataType.Currency,
        unit: Unit.CurrencySign,
    },
    {
        name: 'CPC',
        value: CampaignGoalKPI.CPC,
        dataType: DataType.Currency,
        unit: Unit.CurrencySign,
    },
    {
        name: 'New Users',
        value: CampaignGoalKPI.NEW_UNIQUE_VISITORS,
        dataType: DataType.Decimal,
        unit: Unit.Percent,
    },
    {
        name: 'CPA - Setup Conversion Tracking',
        value: CampaignGoalKPI.CPA,
        dataType: DataType.Currency,
        unit: Unit.CurrencySign,
    },
    {
        name: 'Cost per Non-Bounced Visit',
        value: CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
        dataType: DataType.Currency,
        unit: Unit.CurrencySign,
    },
    {
        name: 'Cost per New Visitor',
        value: CampaignGoalKPI.CP_NEW_VISITOR,
        dataType: DataType.Currency,
        unit: Unit.CurrencySign,
    },
    {
        name: 'Cost per Pageview',
        value: CampaignGoalKPI.CP_PAGE_VIEW,
        dataType: DataType.Currency,
        unit: Unit.CurrencySign,
    },
    {
        name: 'Cost per Completed Video View',
        value: CampaignGoalKPI.CPCV,
        dataType: DataType.Currency,
        unit: Unit.CurrencySign,
    },
];

export const CAMPAIGN_CONVERSION_GOAL_TYPES: CampaignConversionGoalTypeConfig[] = [
    {
        name: 'Pixel',
        value: CampaignConversionGoalType.PIXEL,
    },
    {
        name: 'Google Analytics',
        value: CampaignConversionGoalType.GA,
    },
    {
        name: 'Adobe Analytics',
        value: CampaignConversionGoalType.OMNITURE,
    },
];

export const CONVERSION_WINDOWS: ConversionWindowConfig[] = [
    {name: '1 day', value: ConversionWindow.LEQ_1_DAY},
    {name: '7 days', value: ConversionWindow.LEQ_7_DAYS},
    {name: '30 days', value: ConversionWindow.LEQ_30_DAYS},
];

export const CAMPAIGN_TRACKING_VALUE_TEXT = {
    [GaTrackingType.EMAIL]: 'Email',
    [GaTrackingType.API]: 'API',
};

export const CAMPAIGN_TYPES: CampaignTypeConfig[] = [
    {
        name: 'Native Ad Campaign',
        value: CampaignType.CONTENT,
    },
    {
        name: 'Native Video Advertising',
        value: CampaignType.VIDEO,
    },
    {
        name: 'Native Conversion Marketing',
        value: CampaignType.CONVERSION,
    },
    {
        name: 'Native Mobile App Advertising',
        value: CampaignType.MOBILE,
    },
    {
        name: 'Display Ad Campaign',
        value: CampaignType.DISPLAY,
    },
];

export const IAB_CATEGORIES: IabCategoryConfig[] = [
    {name: 'Uncategorized (IAB24)', value: IabCategory.IAB24},
    {
        name: 'Books & Literature (IAB1-1)',
        value: IabCategory.IAB1_1,
    },
    {
        name: 'Celebrity Fan/Gossip (IAB1-2)',
        value: IabCategory.IAB1_2,
    },
    {name: 'Fine Art (IAB1-3)', value: IabCategory.IAB1_3},
    {name: 'Humor (IAB1-4)', value: IabCategory.IAB1_4},
    {name: 'Movies (IAB1-5)', value: IabCategory.IAB1_5},
    {name: 'Music (IAB1-6)', value: IabCategory.IAB1_6},
    {name: 'Television (IAB1-7)', value: IabCategory.IAB1_7},
    {name: 'Auto Parts (IAB2-1)', value: IabCategory.IAB2_1},
    {name: 'Auto Repair (IAB2-2)', value: IabCategory.IAB2_2},
    {
        name: 'Buying/Selling Cars (IAB2-3)',
        value: IabCategory.IAB2_3,
    },
    {name: 'Car Culture (IAB2-4)', value: IabCategory.IAB2_4},
    {
        name: 'Certified Pre-Owned (IAB2-5)',
        value: IabCategory.IAB2_5,
    },
    {name: 'Convertible (IAB2-6)', value: IabCategory.IAB2_6},
    {name: 'Coupe (IAB2-7)', value: IabCategory.IAB2_7},
    {name: 'Crossover (IAB2-8)', value: IabCategory.IAB2_8},
    {name: 'Diesel (IAB2-9)', value: IabCategory.IAB2_9},
    {
        name: 'Electric Vehicle (IAB2-10)',
        value: IabCategory.IAB2_10,
    },
    {name: 'Hatchback (IAB2-11)', value: IabCategory.IAB2_11},
    {name: 'Hybrid (IAB2-12)', value: IabCategory.IAB2_12},
    {name: 'Luxury (IAB2-13)', value: IabCategory.IAB2_13},
    {name: 'MiniVan (IAB2-14)', value: IabCategory.IAB2_14},
    {
        name: 'Mororcycles (IAB2-15)',
        value: IabCategory.IAB2_15,
    },
    {
        name: 'Off-Road Vehicles (IAB2-16)',
        value: IabCategory.IAB2_16,
    },
    {
        name: 'Performance Vehicles (IAB2-17)',
        value: IabCategory.IAB2_17,
    },
    {name: 'Pickup (IAB2-18)', value: IabCategory.IAB2_18},
    {
        name: 'Road-Side Assistance (IAB2-19)',
        value: IabCategory.IAB2_19,
    },
    {name: 'Sedan (IAB2-20)', value: IabCategory.IAB2_20},
    {
        name: 'Trucks & Accessories (IAB2-21)',
        value: IabCategory.IAB2_21,
    },
    {
        name: 'Vintage Cars (IAB2-22)',
        value: IabCategory.IAB2_22,
    },
    {name: 'Wagon (IAB2-23)', value: IabCategory.IAB2_23},
    {name: 'Advertising (IAB3-1)', value: IabCategory.IAB3_1},
    {name: 'Agriculture (IAB3-2)', value: IabCategory.IAB3_2},
    {
        name: 'Biotech/Biomedical (IAB3-3)',
        value: IabCategory.IAB3_3,
    },
    {
        name: 'Business Software (IAB3-4)',
        value: IabCategory.IAB3_4,
    },
    {
        name: 'Construction (IAB3-5)',
        value: IabCategory.IAB3_5,
    },
    {name: 'Forestry (IAB3-6)', value: IabCategory.IAB3_6},
    {name: 'Government (IAB3-7)', value: IabCategory.IAB3_7},
    {
        name: 'Green Solutions (IAB3-8)',
        value: IabCategory.IAB3_8,
    },
    {
        name: 'Human Resources (IAB3-9)',
        value: IabCategory.IAB3_9,
    },
    {name: 'Logistics (IAB3-10)', value: IabCategory.IAB3_10},
    {name: 'Marketing (IAB3-11)', value: IabCategory.IAB3_11},
    {name: 'Metals (IAB3-12)', value: IabCategory.IAB3_12},
    {
        name: 'Career Planning (IAB4-1)',
        value: IabCategory.IAB4_1,
    },
    {name: 'College (IAB4-2)', value: IabCategory.IAB4_2},
    {
        name: 'Financial Aid (IAB4-3)',
        value: IabCategory.IAB4_3,
    },
    {name: 'Job Fairs (IAB4-4)', value: IabCategory.IAB4_4},
    {name: 'Job Search (IAB4-5)', value: IabCategory.IAB4_5},
    {
        name: 'Resume Writing/Advice (IAB4-6)',
        value: IabCategory.IAB4_6,
    },
    {name: 'Nursing (IAB4-7)', value: IabCategory.IAB4_7},
    {
        name: 'Scholarships (IAB4-8)',
        value: IabCategory.IAB4_8,
    },
    {
        name: 'Telecommuting (IAB4-9)',
        value: IabCategory.IAB4_9,
    },
    {
        name: 'U.S. Military (IAB4-10)',
        value: IabCategory.IAB4_10,
    },
    {
        name: 'Career Advice (IAB4-11)',
        value: IabCategory.IAB4_11,
    },
    {
        name: '7-12 Education (IAB5-1)',
        value: IabCategory.IAB5_1,
    },
    {
        name: 'Adult Education (IAB5-2)',
        value: IabCategory.IAB5_2,
    },
    {name: 'Art History (IAB5-3)', value: IabCategory.IAB5_3},
    {
        name: 'Colledge Administration (IAB5-4)',
        value: IabCategory.IAB5_4,
    },
    {
        name: 'College Life (IAB5-5)',
        value: IabCategory.IAB5_5,
    },
    {
        name: 'Distance Learning (IAB5-6)',
        value: IabCategory.IAB5_6,
    },
    {
        name: 'English as a 2nd Language (IAB5-7)',
        value: IabCategory.IAB5_7,
    },
    {
        name: 'Language Learning (IAB5-8)',
        value: IabCategory.IAB5_8,
    },
    {
        name: 'Graduate School (IAB5-9)',
        value: IabCategory.IAB5_9,
    },
    {
        name: 'Homeschooling (IAB5-10)',
        value: IabCategory.IAB5_10,
    },
    {
        name: 'Homework/Study Tips (IAB5-11)',
        value: IabCategory.IAB5_11,
    },
    {
        name: 'K-6 Educators (IAB5-12)',
        value: IabCategory.IAB5_12,
    },
    {
        name: 'Private School (IAB5-13)',
        value: IabCategory.IAB5_13,
    },
    {
        name: 'Special Education (IAB5-14)',
        value: IabCategory.IAB5_14,
    },
    {
        name: 'Studying Business (IAB5-15)',
        value: IabCategory.IAB5_15,
    },
    {name: 'Adoption (IAB6-1)', value: IabCategory.IAB6_1},
    {
        name: 'Babies & Toddlers (IAB6-2)',
        value: IabCategory.IAB6_2,
    },
    {
        name: 'Daycare/Pre School (IAB6-3)',
        value: IabCategory.IAB6_3,
    },
    {
        name: 'Family Internet (IAB6-4)',
        value: IabCategory.IAB6_4,
    },
    {
        name: 'Parenting - K-6 Kids (IAB6-5)',
        value: IabCategory.IAB6_5,
    },
    {
        name: 'Parenting teens (IAB6-6)',
        value: IabCategory.IAB6_6,
    },
    {name: 'Pregnancy (IAB6-7)', value: IabCategory.IAB6_7},
    {
        name: 'Special Needs Kids (IAB6-8)',
        value: IabCategory.IAB6_8,
    },
    {name: 'Eldercare (IAB6-9)', value: IabCategory.IAB6_9},
    {name: 'Exercise (IAB7-1)', value: IabCategory.IAB7_1},
    {name: 'A.D.D. (IAB7-2)', value: IabCategory.IAB7_2},
    {name: 'AIDS/HIV (IAB7-3)', value: IabCategory.IAB7_3},
    {name: 'Allergies (IAB7-4)', value: IabCategory.IAB7_4},
    {
        name: 'Alternative Medicine (IAB7-5)',
        value: IabCategory.IAB7_5,
    },
    {name: 'Arthritis (IAB7-6)', value: IabCategory.IAB7_6},
    {name: 'Asthma (IAB7-7)', value: IabCategory.IAB7_7},
    {name: 'Autism/PDD (IAB7-8)', value: IabCategory.IAB7_8},
    {
        name: 'Bipolar Disorder (IAB7-9)',
        value: IabCategory.IAB7_9,
    },
    {
        name: 'Brain Tumor (IAB7-10)',
        value: IabCategory.IAB7_10,
    },
    {name: 'Cancer (IAB7-11)', value: IabCategory.IAB7_11},
    {
        name: 'Cholesterol (IAB7-12)',
        value: IabCategory.IAB7_12,
    },
    {
        name: 'Chronic Fatigue Syndrome (IAB7-13)',
        value: IabCategory.IAB7_13,
    },
    {
        name: 'Chronic Pain (IAB7-14)',
        value: IabCategory.IAB7_14,
    },
    {
        name: 'Cold & Flu (IAB7-15)',
        value: IabCategory.IAB7_15,
    },
    {name: 'Deafness (IAB7-16)', value: IabCategory.IAB7_16},
    {
        name: 'Dental Care (IAB7-17)',
        value: IabCategory.IAB7_17,
    },
    {
        name: 'Depression (IAB7-18)',
        value: IabCategory.IAB7_18,
    },
    {
        name: 'Dermatology (IAB7-19)',
        value: IabCategory.IAB7_19,
    },
    {name: 'Diabetes (IAB7-20)', value: IabCategory.IAB7_20},
    {name: 'Epilepsy (IAB7-21)', value: IabCategory.IAB7_21},
    {
        name: 'GERD/Acid Reflux (IAB7-22)',
        value: IabCategory.IAB7_22,
    },
    {
        name: 'Headaches/Migraines (IAB7-23)',
        value: IabCategory.IAB7_23,
    },
    {
        name: 'Heart Disease (IAB7-24)',
        value: IabCategory.IAB7_24,
    },
    {
        name: 'Herbs for Health (IAB7-25)',
        value: IabCategory.IAB7_25,
    },
    {
        name: 'Holistic Healing (IAB7-26)',
        value: IabCategory.IAB7_26,
    },
    {
        name: "IBS/Crohn's Disease (IAB7-27)",
        value: IabCategory.IAB7_27,
    },
    {
        name: 'Incest/Abuse Support (IAB7-28)',
        value: IabCategory.IAB7_28,
    },
    {
        name: 'Incontinence (IAB7-29)',
        value: IabCategory.IAB7_29,
    },
    {
        name: 'Infertility (IAB7-30)',
        value: IabCategory.IAB7_30,
    },
    {
        name: "Men's Health (IAB7-31)",
        value: IabCategory.IAB7_31,
    },
    {name: 'Nutrition (IAB7-32)', value: IabCategory.IAB7_32},
    {
        name: 'Orthopedics (IAB7-33)',
        value: IabCategory.IAB7_33,
    },
    {
        name: 'Panic/Anxiety Disorders (IAB7-34)',
        value: IabCategory.IAB7_34,
    },
    {
        name: 'Pediatrics (IAB7-35)',
        value: IabCategory.IAB7_35,
    },
    {
        name: 'Physical Therapy (IAB7-36)',
        value: IabCategory.IAB7_36,
    },
    {
        name: 'Psychology/Psychiatry (IAB7-37)',
        value: IabCategory.IAB7_37,
    },
    {
        name: 'Senior Health (IAB7-38)',
        value: IabCategory.IAB7_38,
    },
    {name: 'Sexuality (IAB7-39)', value: IabCategory.IAB7_39},
    {
        name: 'Sleep Disorders (IAB7-40)',
        value: IabCategory.IAB7_40,
    },
    {
        name: 'Smoking Cessation (IAB7-41)',
        value: IabCategory.IAB7_41,
    },
    {
        name: 'Substance Abuse (IAB7-42)',
        value: IabCategory.IAB7_42,
    },
    {
        name: 'Thyroid Disease (IAB7-43)',
        value: IabCategory.IAB7_43,
    },
    {
        name: 'Weight Loss (IAB7-44)',
        value: IabCategory.IAB7_44,
    },
    {
        name: "Women's Health (IAB7-45)",
        value: IabCategory.IAB7_45,
    },
    {
        name: 'American Cuisine (IAB8-1)',
        value: IabCategory.IAB8_1,
    },
    {
        name: 'Barbecues & Grilling (IAB8-2)',
        value: IabCategory.IAB8_2,
    },
    {
        name: 'Cajun/Creole (IAB8-3)',
        value: IabCategory.IAB8_3,
    },
    {
        name: 'Chinese Cuisine (IAB8-4)',
        value: IabCategory.IAB8_4,
    },
    {
        name: 'Cocktails/Beer (IAB8-5)',
        value: IabCategory.IAB8_5,
    },
    {name: 'Coffee/Tea (IAB8-6)', value: IabCategory.IAB8_6},
    {
        name: 'Cuisine-Specific (IAB8-7)',
        value: IabCategory.IAB8_7,
    },
    {
        name: 'Desserts & Baking (IAB8-8)',
        value: IabCategory.IAB8_8,
    },
    {name: 'Dining Out (IAB8-9)', value: IabCategory.IAB8_9},
    {
        name: 'Food Allergies (IAB8-10)',
        value: IabCategory.IAB8_10,
    },
    {
        name: 'French Cuisine (IAB8-11)',
        value: IabCategory.IAB8_11,
    },
    {
        name: 'Health/Lowfat Cooking (IAB8-12)',
        value: IabCategory.IAB8_12,
    },
    {
        name: 'Italian Cuisine (IAB8-13)',
        value: IabCategory.IAB8_13,
    },
    {
        name: 'Japanese Cuisine (IAB8-14)',
        value: IabCategory.IAB8_14,
    },
    {
        name: 'Mexican Cuisine (IAB8-15)',
        value: IabCategory.IAB8_15,
    },
    {name: 'Vegan (IAB8-16)', value: IabCategory.IAB8_16},
    {
        name: 'Vegetarian (IAB8-17)',
        value: IabCategory.IAB8_17,
    },
    {name: 'Wine (IAB8-18)', value: IabCategory.IAB8_18},
    {
        name: 'Art/Technology (IAB9-1)',
        value: IabCategory.IAB9_1,
    },
    {
        name: 'Arts & Crafts (IAB9-2)',
        value: IabCategory.IAB9_2,
    },
    {name: 'Beadwork (IAB9-3)', value: IabCategory.IAB9_3},
    {
        name: 'Birdwatching (IAB9-4)',
        value: IabCategory.IAB9_4,
    },
    {
        name: 'Board Games/Puzzles (IAB9-5)',
        value: IabCategory.IAB9_5,
    },
    {
        name: 'Candle & Soap Making (IAB9-6)',
        value: IabCategory.IAB9_6,
    },
    {name: 'Card Games (IAB9-7)', value: IabCategory.IAB9_7},
    {name: 'Chess (IAB9-8)', value: IabCategory.IAB9_8},
    {name: 'Cigars (IAB9-9)', value: IabCategory.IAB9_9},
    {
        name: 'Collecting (IAB9-10)',
        value: IabCategory.IAB9_10,
    },
    {
        name: 'Comic Books (IAB9-11)',
        value: IabCategory.IAB9_11,
    },
    {
        name: 'Drawing/Sketching (IAB9-12)',
        value: IabCategory.IAB9_12,
    },
    {
        name: 'Freelance Writing (IAB9-13)',
        value: IabCategory.IAB9_13,
    },
    {name: 'Genealogy (IAB9-14)', value: IabCategory.IAB9_14},
    {
        name: 'Getting Published (IAB9-15)',
        value: IabCategory.IAB9_15,
    },
    {name: 'Guitar (IAB9-16)', value: IabCategory.IAB9_16},
    {
        name: 'Home Recording (IAB9-17)',
        value: IabCategory.IAB9_17,
    },
    {
        name: 'Investors & Patents (IAB9-18)',
        value: IabCategory.IAB9_18,
    },
    {
        name: 'Jewelry Making (IAB9-19)',
        value: IabCategory.IAB9_19,
    },
    {
        name: 'Magic & Illusion (IAB9-20)',
        value: IabCategory.IAB9_20,
    },
    {
        name: 'Needlework (IAB9-21)',
        value: IabCategory.IAB9_21,
    },
    {name: 'Painting (IAB9-22)', value: IabCategory.IAB9_22},
    {
        name: 'Photography (IAB9-23)',
        value: IabCategory.IAB9_23,
    },
    {name: 'Radio (IAB9-24)', value: IabCategory.IAB9_24},
    {
        name: 'Roleplaying Games (IAB9-25)',
        value: IabCategory.IAB9_25,
    },
    {
        name: 'Sci-Fi & Fantasy (IAB9-26)',
        value: IabCategory.IAB9_26,
    },
    {
        name: 'Scrapbooking (IAB9-27)',
        value: IabCategory.IAB9_27,
    },
    {
        name: 'Screenwriting (IAB9-28)',
        value: IabCategory.IAB9_28,
    },
    {
        name: 'Stamps & Coins (IAB9-29)',
        value: IabCategory.IAB9_29,
    },
    {
        name: 'Video & Computer Games (IAB9-30)',
        value: IabCategory.IAB9_30,
    },
    {
        name: 'Woodworking (IAB9-31)',
        value: IabCategory.IAB9_31,
    },
    {
        name: 'Appliances (IAB10-1)',
        value: IabCategory.IAB10_1,
    },
    {
        name: 'Entertaining (IAB10-2)',
        value: IabCategory.IAB10_2,
    },
    {
        name: 'Environmental Safety (IAB10-3)',
        value: IabCategory.IAB10_3,
    },
    {name: 'Gardening (IAB10-4)', value: IabCategory.IAB10_4},
    {
        name: 'Home Repair (IAB10-5)',
        value: IabCategory.IAB10_5,
    },
    {
        name: 'Home Theater (IAB10-6)',
        value: IabCategory.IAB10_6,
    },
    {
        name: 'Interior Decorating (IAB10-7)',
        value: IabCategory.IAB10_7,
    },
    {
        name: 'Landscaping (IAB10-8)',
        value: IabCategory.IAB10_8,
    },
    {
        name: 'Remodeling & Construction (IAB10-9)',
        value: IabCategory.IAB10_9,
    },
    {
        name: 'Immigration (IAB11-1)',
        value: IabCategory.IAB11_1,
    },
    {
        name: 'Legal Issues (IAB11-2)',
        value: IabCategory.IAB11_2,
    },
    {
        name: 'U.S. Government Resources (IAB11-3)',
        value: IabCategory.IAB11_3,
    },
    {name: 'Politics (IAB11-4)', value: IabCategory.IAB11_4},
    {
        name: 'Commentary (IAB11-5)',
        value: IabCategory.IAB11_5,
    },
    {
        name: 'International News (IAB12-1)',
        value: IabCategory.IAB12_1,
    },
    {
        name: 'National News (IAB12-2)',
        value: IabCategory.IAB12_2,
    },
    {
        name: 'Local News (IAB12-3)',
        value: IabCategory.IAB12_3,
    },
    {
        name: 'Beginning Investing (IAB13-1)',
        value: IabCategory.IAB13_1,
    },
    {
        name: 'Credit/Debt & Loans (IAB13-2)',
        value: IabCategory.IAB13_2,
    },
    {
        name: 'Financial News (IAB13-3)',
        value: IabCategory.IAB13_3,
    },
    {
        name: 'Financial Planning (IAB13-4)',
        value: IabCategory.IAB13_4,
    },
    {
        name: 'Hedge Fund (IAB13-5)',
        value: IabCategory.IAB13_5,
    },
    {name: 'Insurance (IAB13-6)', value: IabCategory.IAB13_6},
    {name: 'Investing (IAB13-7)', value: IabCategory.IAB13_7},
    {
        name: 'Mutual Funds (IAB13-8)',
        value: IabCategory.IAB13_8,
    },
    {name: 'Options (IAB13-9)', value: IabCategory.IAB13_9},
    {
        name: 'Retirement Planning (IAB13-10)',
        value: IabCategory.IAB13_10,
    },
    {name: 'Stocks (IAB13-11)', value: IabCategory.IAB13_11},
    {
        name: 'Tax Planning (IAB13-12)',
        value: IabCategory.IAB13_12,
    },
    {name: 'Dating (IAB14-1)', value: IabCategory.IAB14_1},
    {
        name: 'Divorce Support (IAB14-2)',
        value: IabCategory.IAB14_2,
    },
    {name: 'Gay Life (IAB14-3)', value: IabCategory.IAB14_3},
    {name: 'Marriage (IAB14-4)', value: IabCategory.IAB14_4},
    {
        name: 'Senior Living (IAB14-5)',
        value: IabCategory.IAB14_5,
    },
    {name: 'Teens (IAB14-6)', value: IabCategory.IAB14_6},
    {name: 'Weddings (IAB14-7)', value: IabCategory.IAB14_7},
    {
        name: 'Ethnic Specific (IAB14-8)',
        value: IabCategory.IAB14_8,
    },
    {name: 'Astrology (IAB15-1)', value: IabCategory.IAB15_1},
    {name: 'Biology (IAB15-2)', value: IabCategory.IAB15_2},
    {name: 'Chemistry (IAB15-3)', value: IabCategory.IAB15_3},
    {name: 'Geology (IAB15-4)', value: IabCategory.IAB15_4},
    {
        name: 'Paranormal Phenomena (IAB15-5)',
        value: IabCategory.IAB15_5,
    },
    {name: 'Physics (IAB15-6)', value: IabCategory.IAB15_6},
    {
        name: 'Space/Astronomy (IAB15-7)',
        value: IabCategory.IAB15_7,
    },
    {name: 'Geography (IAB15-8)', value: IabCategory.IAB15_8},
    {name: 'Botany (IAB15-9)', value: IabCategory.IAB15_9},
    {name: 'Weather (IAB15-10)', value: IabCategory.IAB15_10},
    {name: 'Aquariums (IAB16-1)', value: IabCategory.IAB16_1},
    {name: 'Birds (IAB16-2)', value: IabCategory.IAB16_2},
    {name: 'Cats (IAB16-3)', value: IabCategory.IAB16_3},
    {name: 'Dogs (IAB16-4)', value: IabCategory.IAB16_4},
    {
        name: 'Large Animals (IAB16-5)',
        value: IabCategory.IAB16_5,
    },
    {name: 'Reptiles (IAB16-6)', value: IabCategory.IAB16_6},
    {
        name: 'Veterinary Medicine (IAB16-7)',
        value: IabCategory.IAB16_7,
    },
    {
        name: 'Auto Racing (IAB17-1)',
        value: IabCategory.IAB17_1,
    },
    {name: 'Baseball (IAB17-2)', value: IabCategory.IAB17_2},
    {name: 'Bicycling (IAB17-3)', value: IabCategory.IAB17_3},
    {
        name: 'Bodybuilding (IAB17-4)',
        value: IabCategory.IAB17_4,
    },
    {name: 'Boxing (IAB17-5)', value: IabCategory.IAB17_5},
    {
        name: 'Canoeing/Kayaking (IAB17-6)',
        value: IabCategory.IAB17_6,
    },
    {
        name: 'Cheerleading (IAB17-7)',
        value: IabCategory.IAB17_7,
    },
    {name: 'Climbing (IAB17-8)', value: IabCategory.IAB17_8},
    {name: 'Cricket (IAB17-9)', value: IabCategory.IAB17_9},
    {
        name: 'Figure Skating (IAB17-10)',
        value: IabCategory.IAB17_10,
    },
    {
        name: 'Fly Fishing (IAB17-11)',
        value: IabCategory.IAB17_11,
    },
    {
        name: 'Football (IAB17-12)',
        value: IabCategory.IAB17_12,
    },
    {
        name: 'Freshwater Fishing (IAB17-13)',
        value: IabCategory.IAB17_13,
    },
    {
        name: 'Game & Fish (IAB17-14)',
        value: IabCategory.IAB17_14,
    },
    {name: 'Golf (IAB17-15)', value: IabCategory.IAB17_15},
    {
        name: 'Horse Racing (IAB17-16)',
        value: IabCategory.IAB17_16,
    },
    {name: 'Horses (IAB17-17)', value: IabCategory.IAB17_17},
    {
        name: 'Hunting/Shooting (IAB17-18)',
        value: IabCategory.IAB17_18,
    },
    {
        name: 'Inline Skating (IAB17-19)',
        value: IabCategory.IAB17_19,
    },
    {
        name: 'Martial Arts (IAB17-20)',
        value: IabCategory.IAB17_20,
    },
    {
        name: 'Mountain Biking (IAB17-21)',
        value: IabCategory.IAB17_21,
    },
    {
        name: 'NASCAR Racing (IAB17-22)',
        value: IabCategory.IAB17_22,
    },
    {
        name: 'Olympics (IAB17-23)',
        value: IabCategory.IAB17_23,
    },
    {
        name: 'Paintball (IAB17-24)',
        value: IabCategory.IAB17_24,
    },
    {
        name: 'Power & Motorcycles (IAB17-25)',
        value: IabCategory.IAB17_25,
    },
    {
        name: 'Pro Basketball (IAB17-26)',
        value: IabCategory.IAB17_26,
    },
    {
        name: 'Pro Ice Hockey (IAB17-27)',
        value: IabCategory.IAB17_27,
    },
    {name: 'Rodeo (IAB17-28)', value: IabCategory.IAB17_28},
    {name: 'Rugby (IAB17-29)', value: IabCategory.IAB17_29},
    {
        name: 'Running/Jogging (IAB17-30)',
        value: IabCategory.IAB17_30,
    },
    {name: 'Sailing (IAB17-31)', value: IabCategory.IAB17_31},
    {
        name: 'Saltwater Fishing (IAB17-32)',
        value: IabCategory.IAB17_32,
    },
    {
        name: 'Scuba Diving (IAB17-33)',
        value: IabCategory.IAB17_33,
    },
    {
        name: 'Skateboarding (IAB17-34)',
        value: IabCategory.IAB17_34,
    },
    {name: 'Skiing (IAB17-35)', value: IabCategory.IAB17_35},
    {
        name: 'Snowboarding (IAB17-36)',
        value: IabCategory.IAB17_36,
    },
    {
        name: 'Surfing/Bodyboarding (IAB17-37)',
        value: IabCategory.IAB17_37,
    },
    {
        name: 'Swimming (IAB17-38)',
        value: IabCategory.IAB17_38,
    },
    {
        name: 'Table Tennis/Ping-Pong (IAB17-39)',
        value: IabCategory.IAB17_39,
    },
    {name: 'Tennis (IAB17-40)', value: IabCategory.IAB17_40},
    {
        name: 'Volleyball (IAB17-41)',
        value: IabCategory.IAB17_41,
    },
    {name: 'Walking (IAB17-42)', value: IabCategory.IAB17_42},
    {
        name: 'Waterski/Wakeboard (IAB17-43)',
        value: IabCategory.IAB17_43,
    },
    {
        name: 'World Soccer (IAB17-44)',
        value: IabCategory.IAB17_44,
    },
    {name: 'Beauty (IAB18-1)', value: IabCategory.IAB18_1},
    {name: 'Body Art (IAB18-2)', value: IabCategory.IAB18_2},
    {name: 'Fashion (IAB18-3)', value: IabCategory.IAB18_3},
    {name: 'Jewelry (IAB18-4)', value: IabCategory.IAB18_4},
    {name: 'Clothing (IAB18-5)', value: IabCategory.IAB18_5},
    {
        name: 'Accessories (IAB18-6)',
        value: IabCategory.IAB18_6,
    },
    {
        name: '3-D Graphics (IAB19-1)',
        value: IabCategory.IAB19_1,
    },
    {name: 'Animation (IAB19-2)', value: IabCategory.IAB19_2},
    {
        name: 'Antivirus Software (IAB19-3)',
        value: IabCategory.IAB19_3,
    },
    {name: 'C/C++ (IAB19-4)', value: IabCategory.IAB19_4},
    {
        name: 'Cameras & Camcorders (IAB19-5)',
        value: IabCategory.IAB19_5,
    },
    {
        name: 'Cell Phones (IAB19-6)',
        value: IabCategory.IAB19_6,
    },
    {
        name: 'Computer Certification (IAB19-7)',
        value: IabCategory.IAB19_7,
    },
    {
        name: 'Computer Networking (IAB19-8)',
        value: IabCategory.IAB19_8,
    },
    {
        name: 'Computer Peripherals (IAB19-9)',
        value: IabCategory.IAB19_9,
    },
    {
        name: 'Computer Reviews (IAB19-10)',
        value: IabCategory.IAB19_10,
    },
    {
        name: 'Data Centers (IAB19-11)',
        value: IabCategory.IAB19_11,
    },
    {
        name: 'Databases (IAB19-12)',
        value: IabCategory.IAB19_12,
    },
    {
        name: 'Desktop Publishing (IAB19-13)',
        value: IabCategory.IAB19_13,
    },
    {
        name: 'Desktop Video (IAB19-14)',
        value: IabCategory.IAB19_14,
    },
    {name: 'Email (IAB19-15)', value: IabCategory.IAB19_15},
    {
        name: 'Graphics Software (IAB19-16)',
        value: IabCategory.IAB19_16,
    },
    {
        name: 'Home Video/DVD (IAB19-17)',
        value: IabCategory.IAB19_17,
    },
    {
        name: 'Internet Technology (IAB19-18)',
        value: IabCategory.IAB19_18,
    },
    {name: 'Java (IAB19-19)', value: IabCategory.IAB19_19},
    {
        name: 'JavaScript (IAB19-20)',
        value: IabCategory.IAB19_20,
    },
    {
        name: 'Mac Support (IAB19-21)',
        value: IabCategory.IAB19_21,
    },
    {
        name: 'MP3/MIDI (IAB19-22)',
        value: IabCategory.IAB19_22,
    },
    {
        name: 'Net Conferencing (IAB19-23)',
        value: IabCategory.IAB19_23,
    },
    {
        name: 'Net for Beginners (IAB19-24)',
        value: IabCategory.IAB19_24,
    },
    {
        name: 'Network Security (IAB19-25)',
        value: IabCategory.IAB19_25,
    },
    {
        name: 'Palmtops/PDAs (IAB19-26)',
        value: IabCategory.IAB19_26,
    },
    {
        name: 'PC Support (IAB19-27)',
        value: IabCategory.IAB19_27,
    },
    {
        name: 'Portable (IAB19-28)',
        value: IabCategory.IAB19_28,
    },
    {
        name: 'Entertainment (IAB19-29)',
        value: IabCategory.IAB19_29,
    },
    {
        name: 'Shareware/Freeware (IAB19-30)',
        value: IabCategory.IAB19_30,
    },
    {name: 'Unix (IAB19-31)', value: IabCategory.IAB19_31},
    {
        name: 'Visual Basic (IAB19-32)',
        value: IabCategory.IAB19_32,
    },
    {
        name: 'Web Clip Art (IAB19-33)',
        value: IabCategory.IAB19_33,
    },
    {
        name: 'Web Design/HTML (IAB19-34)',
        value: IabCategory.IAB19_34,
    },
    {
        name: 'Web Search (IAB19-35)',
        value: IabCategory.IAB19_35,
    },
    {name: 'Windows (IAB19-36)', value: IabCategory.IAB19_36},
    {
        name: 'Adventure Travel (IAB20-1)',
        value: IabCategory.IAB20_1,
    },
    {name: 'Africa (IAB20-2)', value: IabCategory.IAB20_2},
    {
        name: 'Air Travel (IAB20-3)',
        value: IabCategory.IAB20_3,
    },
    {
        name: 'Australia & New Zealand (IAB20-4)',
        value: IabCategory.IAB20_4,
    },
    {
        name: 'Bed & Breakfasts (IAB20-5)',
        value: IabCategory.IAB20_5,
    },
    {
        name: 'Budget Travel (IAB20-6)',
        value: IabCategory.IAB20_6,
    },
    {
        name: 'Business Travel (IAB20-7)',
        value: IabCategory.IAB20_7,
    },
    {
        name: 'By US Locale (IAB20-8)',
        value: IabCategory.IAB20_8,
    },
    {name: 'Camping (IAB20-9)', value: IabCategory.IAB20_9},
    {name: 'Canada (IAB20-10)', value: IabCategory.IAB20_10},
    {
        name: 'Caribbean (IAB20-11)',
        value: IabCategory.IAB20_11,
    },
    {name: 'Cruises (IAB20-12)', value: IabCategory.IAB20_12},
    {
        name: 'Eastern Europe (IAB20-13)',
        value: IabCategory.IAB20_13,
    },
    {name: 'Europe (IAB20-14)', value: IabCategory.IAB20_14},
    {name: 'France (IAB20-15)', value: IabCategory.IAB20_15},
    {name: 'Greece (IAB20-16)', value: IabCategory.IAB20_16},
    {
        name: 'Honeymoons/Getaways (IAB20-17)',
        value: IabCategory.IAB20_17,
    },
    {name: 'Hotels (IAB20-18)', value: IabCategory.IAB20_18},
    {name: 'Italy (IAB20-19)', value: IabCategory.IAB20_19},
    {name: 'Japan (IAB20-20)', value: IabCategory.IAB20_20},
    {
        name: 'Mexico & Central America (IAB20-21)',
        value: IabCategory.IAB20_21,
    },
    {
        name: 'National Parks (IAB20-22)',
        value: IabCategory.IAB20_22,
    },
    {
        name: 'South America (IAB20-23)',
        value: IabCategory.IAB20_23,
    },
    {name: 'Spas (IAB20-24)', value: IabCategory.IAB20_24},
    {
        name: 'Theme Parks (IAB20-25)',
        value: IabCategory.IAB20_25,
    },
    {
        name: 'Traveling with Kids (IAB20-26)',
        value: IabCategory.IAB20_26,
    },
    {
        name: 'United Kingdom (IAB20-27)',
        value: IabCategory.IAB20_27,
    },
    {
        name: 'Apartments (IAB21-1)',
        value: IabCategory.IAB21_1,
    },
    {
        name: 'Architects (IAB21-2)',
        value: IabCategory.IAB21_2,
    },
    {
        name: 'Buying/Selling Homes (IAB21-3)',
        value: IabCategory.IAB21_3,
    },
    {
        name: 'Contests & Freebies (IAB22-1)',
        value: IabCategory.IAB22_1,
    },
    {name: 'Couponing (IAB22-2)', value: IabCategory.IAB22_2},
    {
        name: 'Comparison (IAB22-3)',
        value: IabCategory.IAB22_3,
    },
    {name: 'Engines (IAB22-4)', value: IabCategory.IAB22_4},
    {
        name: 'Alternative Religions (IAB23-1)',
        value: IabCategory.IAB23_1,
    },
    {
        name: 'Atheism/Agnosticism (IAB23-2)',
        value: IabCategory.IAB23_2,
    },
    {name: 'Buddhism (IAB23-3)', value: IabCategory.IAB23_3},
    {
        name: 'Catholicism (IAB23-4)',
        value: IabCategory.IAB23_4,
    },
    {
        name: 'Christianity (IAB23-5)',
        value: IabCategory.IAB23_5,
    },
    {name: 'Hinduism (IAB23-6)', value: IabCategory.IAB23_6},
    {name: 'Islam (IAB23-7)', value: IabCategory.IAB23_7},
    {name: 'Judaism (IAB23-8)', value: IabCategory.IAB23_8},
    {
        name: 'Latter-Day Saints (IAB23-9)',
        value: IabCategory.IAB23_9,
    },
    {
        name: 'Pagan/Wiccan (IAB23-10)',
        value: IabCategory.IAB23_10,
    },
    {
        name: 'Unmoderated UGC (IAB25-1)',
        value: IabCategory.IAB25_1,
    },
    {
        name: 'Extreme Graphic/Explicit Violence (IAB25-2)',
        value: IabCategory.IAB25_2,
    },
    {
        name: 'Pornography (IAB25-3)',
        value: IabCategory.IAB25_3,
    },
    {
        name: 'Profane Content (IAB25-4)',
        value: IabCategory.IAB25_4,
    },
    {
        name: 'Hate Content (IAB25-5)',
        value: IabCategory.IAB25_5,
    },
    {
        name: 'Under Construction (IAB25-6)',
        value: IabCategory.IAB25_6,
    },
    {
        name: 'Incentivized (IAB25-7)',
        value: IabCategory.IAB25_7,
    },
    {
        name: 'Illegal Content (IAB26-1)',
        value: IabCategory.IAB26_1,
    },
    {name: 'Warez (IAB26-2)', value: IabCategory.IAB26_2},
    {
        name: 'Spyware/Malware (IAB26-3)',
        value: IabCategory.IAB26_3,
    },
    {
        name: 'CopyrightInfringement (IAB26-4)',
        value: IabCategory.IAB26_4,
    },
];

export const LANGUAGES: LanguageConfig[] = [
    {name: 'English', value: Language.ENGLISH},
    {name: 'German', value: Language.GERMAN},
    {name: 'Greek', value: Language.GREEK},
    {name: 'Arabic', value: Language.ARABIC},
    {name: 'Spanish', value: Language.SPANISH},
    {name: 'French', value: Language.FRENCH},
    {name: 'Indonesian', value: Language.INDONESIAN},
    {name: 'Italian', value: Language.ITALIAN},
    {name: 'Japanese', value: Language.JAPANESE},
    {name: 'Malay', value: Language.MALAY},
    {name: 'Dutch', value: Language.DUTCH},
    {name: 'Portuguese', value: Language.PORTUGUESE},
    {name: 'Romanian', value: Language.ROMANIAN},
    {name: 'Russian', value: Language.RUSSIAN},
    {name: 'Swedish', value: Language.SWEDISH},
    {name: 'Turkish', value: Language.TURKISH},
    {name: 'Vietnamese', value: Language.VIETNAMESE},
    {
        name: 'Simplified Chinese',
        value: Language.SIMPLIFIED_CHINESE,
    },
    {
        name: 'Traditional Chinese',
        value: Language.TRADITIONAL_CHINESE,
    },
    {name: 'Other', value: Language.OTHER},
];
