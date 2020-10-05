import {Level, Breakdown, BreakdownParam} from '../../app.constants';
import {GridColumnTypes} from './analytics.constants';

export const DEFAULT_BREAKDOWN = {
    [Level.ALL_ACCOUNTS]: Breakdown.ACCOUNT,
    [Level.ACCOUNTS]: Breakdown.CAMPAIGN,
    [Level.CAMPAIGNS]: Breakdown.AD_GROUP,
    [Level.AD_GROUPS]: Breakdown.CONTENT_AD,
};

export const BREAKDOWN_PARAM_TO_BREAKDOWN_MAP = {
    [BreakdownParam.SOURCES]: Breakdown.MEDIA_SOURCE,
    [BreakdownParam.COUNTRY]: Breakdown.COUNTRY,
    [BreakdownParam.STATE]: Breakdown.STATE,
    [BreakdownParam.DMA]: Breakdown.DMA,
    [BreakdownParam.DEVICE]: Breakdown.DEVICE,
    [BreakdownParam.ENVIRONMENT]: Breakdown.ENVIRONMENT,
    [BreakdownParam.OPERATING_SYSTEM]: Breakdown.OPERATING_SYSTEM,
    [BreakdownParam.PUBLISHERS]: Breakdown.PUBLISHER,
    [BreakdownParam.PLACEMENTS]: Breakdown.PLACEMENT,
    [BreakdownParam.INSIGHTS]: Breakdown.INSIGHTS,
};

export const BASE_GRID_COLUMN_TYPES: GridColumnTypes[] = [
    GridColumnTypes.TEXT,
    GridColumnTypes.PERCENT,
    GridColumnTypes.NUMBER,
    GridColumnTypes.CURRENCY,
    GridColumnTypes.SECONDS,
    GridColumnTypes.DATE_TIME,
];

export const EXTERNAL_LINK_COLUMN_TYPES: GridColumnTypes[] = [
    GridColumnTypes.ICON_LINK,
    GridColumnTypes.VISIBLE_LINK,
    GridColumnTypes.TEXT_LINK,
];
