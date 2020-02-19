import {
    Level,
    LevelStateParam,
    Breakdown,
    BreakdownStateParam,
    EntityType,
} from '../../app.constants';

export const DEFAULT_BREAKDOWN = {
    [Level.ALL_ACCOUNTS]: Breakdown.ACCOUNT,
    [Level.ACCOUNTS]: Breakdown.CAMPAIGN,
    [Level.CAMPAIGNS]: Breakdown.AD_GROUP,
    [Level.AD_GROUPS]: Breakdown.CONTENT_AD,
};

export const LEVEL_STATE_PARAM_TO_LEVEL_MAP = {
    [LevelStateParam.ACCOUNTS]: Level.ALL_ACCOUNTS,
    [LevelStateParam.ACCOUNT]: Level.ACCOUNTS,
    [LevelStateParam.CAMPAIGN]: Level.CAMPAIGNS,
    [LevelStateParam.AD_GROUP]: Level.AD_GROUPS,
};

export const BREAKDOWN_STATE_PARAM_TO_BREAKDOWN_MAP = {
    [BreakdownStateParam.SOURCES]: Breakdown.MEDIA_SOURCE,
    [BreakdownStateParam.COUNTRY]: Breakdown.COUNTRY,
    [BreakdownStateParam.STATE]: Breakdown.STATE,
    [BreakdownStateParam.DMA]: Breakdown.DMA,
    [BreakdownStateParam.DEVICE]: Breakdown.DEVICE,
    [BreakdownStateParam.ENVIRONMENT]: Breakdown.ENVIRONMENT,
    [BreakdownStateParam.OPERATING_SYSTEM]: Breakdown.OPERATING_SYSTEM,
    [BreakdownStateParam.PUBLISHERS]: Breakdown.PUBLISHER,
    [BreakdownStateParam.INSIGHTS]: Breakdown.INSIGHTS,
};

export const LEVEL_TO_ENTITY_TYPE_MAP = {
    [Level.ACCOUNTS]: EntityType.ACCOUNT,
    [Level.CAMPAIGNS]: EntityType.CAMPAIGN,
    [Level.AD_GROUPS]: EntityType.AD_GROUP,
};
