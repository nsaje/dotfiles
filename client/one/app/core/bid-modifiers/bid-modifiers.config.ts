import {APP_CONFIG} from '../../app.config';
import {BidModifierType} from '../../app.constants';

const adGroupApiUrl = `${APP_CONFIG.apiRestUrl}/v1/adgroups`;
const adGroupInternalApiUrl = `${APP_CONFIG.apiRestInternalUrl}/adgroups`;

export const BID_MODIFIER_CONFIG = {
    requests: {
        save: {
            name: 'save',
            url: `${adGroupApiUrl}/`,
        },
        import: {
            name: 'import',
            url: `${adGroupInternalApiUrl}/`,
        },
        validateFile: {
            name: 'validateFile',
            url: `${adGroupInternalApiUrl}/`,
        },
    },
};

export const BID_MODIFIER_TYPE_NAME_MAP = {
    [BidModifierType.PUBLISHER]: 'Publisher',
    [BidModifierType.SOURCE]: 'Source',
    [BidModifierType.DEVICE]: 'Device',
    [BidModifierType.OPERATING_SYSTEM]: 'Operating System',
    [BidModifierType.PLACEMENT]: 'Placement',
    [BidModifierType.COUNTRY]: 'Country',
    [BidModifierType.STATE]: 'State / Region',
    [BidModifierType.DMA]: 'DMA',
    [BidModifierType.AD]: 'Content Ad',
    [BidModifierType.DAY_HOUR]: 'Day - Hour',
};
