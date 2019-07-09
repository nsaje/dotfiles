import {
    EntityType,
    CampaignConversionGoalType,
    ConversionWindow,
    Unit,
    DataType,
} from '../../app.constants';
import {CampaignGoalKPI} from '../../app.constants';
import {CampaignGoalKPIConfig} from './types/campaign-goal-kpi-config';
import {CampaignConversionGoalTypeConfig} from './types/campaign-conversion-goal-type-config';
import {ConversionWindowConfig} from '../../core/conversion-pixels/types/conversion-windows-config';

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
