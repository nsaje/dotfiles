import {
    Breakdown,
    SettingsState,
    PublisherTargetingStatus,
} from '../../../../../app.constants';
import {GridColumnTypes} from '../../../analytics.constants';
import {EntityStatus} from './grid-bridge.component.constants';

export const RESIZABLE_GRID_COLUMN_TYPES: GridColumnTypes[] = [
    GridColumnTypes.BREAKDOWN,
    GridColumnTypes.TEXT,
    GridColumnTypes.PERCENT,
    GridColumnTypes.NUMBER,
    GridColumnTypes.DATE_TIME,
    GridColumnTypes.SECONDS,
    GridColumnTypes.CURRENCY,
    GridColumnTypes.EXTERNAL_LINK,
    GridColumnTypes.ICON_LINK,
    GridColumnTypes.VISIBLE_LINK,
    GridColumnTypes.TEXT_LINK,
    GridColumnTypes.INTERNAL_LINK,
];

export const PINNED_GRID_COLUMN_TYPES: GridColumnTypes[] = [
    GridColumnTypes.CHECKBOX,
    GridColumnTypes.ACTIONS,
    GridColumnTypes.BREAKDOWN,
];

export const METRIC_GRID_COLUMN_TYPES: GridColumnTypes[] = [
    GridColumnTypes.NUMBER,
    GridColumnTypes.CURRENCY,
    GridColumnTypes.PERCENT,
];

export const BREAKDOWN_TO_STATUS_CONFIG: {
    [key in Breakdown]?:
        | {
              [key in SettingsState]: EntityStatus;
          }
        | {
              [key in PublisherTargetingStatus]: EntityStatus;
          };
} = {
    [Breakdown.ACCOUNT]: {
        [SettingsState.ACTIVE]: EntityStatus.ACTIVE,
        [SettingsState.INACTIVE]: EntityStatus.PAUSED,
    },
    [Breakdown.CAMPAIGN]: {
        [SettingsState.ACTIVE]: EntityStatus.ACTIVE,
        [SettingsState.INACTIVE]: EntityStatus.PAUSED,
    },
    [Breakdown.AD_GROUP]: {
        [SettingsState.ACTIVE]: EntityStatus.ACTIVE,
        [SettingsState.INACTIVE]: EntityStatus.PAUSED,
    },
    [Breakdown.CONTENT_AD]: {
        [SettingsState.ACTIVE]: EntityStatus.ACTIVE,
        [SettingsState.INACTIVE]: EntityStatus.PAUSED,
    },
    [Breakdown.PUBLISHER]: {
        [PublisherTargetingStatus.UNLISTED]: EntityStatus.ACTIVE,
        [PublisherTargetingStatus.BLACKLISTED]: EntityStatus.BLACKLISTED,
        [PublisherTargetingStatus.WHITELISTED]: EntityStatus.WHITELISTED,
    },
    [Breakdown.PLACEMENT]: {
        [PublisherTargetingStatus.UNLISTED]: EntityStatus.ACTIVE,
        [PublisherTargetingStatus.BLACKLISTED]: EntityStatus.BLACKLISTED,
        [PublisherTargetingStatus.WHITELISTED]: EntityStatus.WHITELISTED,
    },
};

export const BREAKDOWN_TO_ACTIONS_COLUMN_WIDTH: {
    [key in Breakdown]?: number;
} = {
    [Breakdown.ACCOUNT]: 90,
    [Breakdown.CAMPAIGN]: 90,
    [Breakdown.AD_GROUP]: 140,
    [Breakdown.CONTENT_AD]: 140,
    [Breakdown.PUBLISHER]: 70,
    [Breakdown.PLACEMENT]: 70,
    [Breakdown.MEDIA_SOURCE]: 70,
    [Breakdown.COUNTRY]: 70,
    [Breakdown.STATE]: 70,
    [Breakdown.DMA]: 70,
    [Breakdown.DEVICE]: 70,
    [Breakdown.ENVIRONMENT]: 70,
    [Breakdown.OPERATING_SYSTEM]: 70,
    [Breakdown.BROWSER]: 70,
    [Breakdown.CONNECTION_TYPE]: 70,
};
