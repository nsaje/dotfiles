import {APP_CONFIG} from '../../../app.config';
import {HttpRequestInfo} from '../../../shared/types/http-request-info';
import {
    PublisherBlacklistLevel,
    PublisherTargetingStatus,
} from '../../../app.constants';
import {PublisherBlacklistAction} from '../types/publisher-blacklist-action';
import {PublisherBlacklistActionLevel} from '../types/publisher-blacklist-action-level';

const publishersApiUrl = `${APP_CONFIG.apiLegacyUrl}/publishers`;

export const PUBLISHERS_CONFIG: {
    requests: {publishers: {[key: string]: HttpRequestInfo}};
    blacklistActions: PublisherBlacklistAction[];
    blacklistLevels: PublisherBlacklistActionLevel[];
} = {
    requests: {
        publishers: {
            updateBlacklistStatuses: {
                name: 'updateBlacklistStatuses',
                url: `${publishersApiUrl}/targeting/`,
            },
        },
    },
    blacklistActions: [
        {
            name: 'Add to',
            status: PublisherTargetingStatus.BLACKLISTED,
        },
        {
            name: 'Remove from',
            status: PublisherTargetingStatus.UNLISTED,
        },
    ],
    blacklistLevels: [
        {
            name: 'ad group',
            level: PublisherBlacklistLevel.ADGROUP,
        },
        {
            name: 'campaign',
            level: PublisherBlacklistLevel.CAMPAIGN,
        },
        {
            name: 'account',
            level: PublisherBlacklistLevel.ACCOUNT,
        },
        {
            name: 'global',
            level: PublisherBlacklistLevel.GLOBAL,
            permissions: [
                'zemauth.can_access_global_publisher_blacklist_status',
            ],
        },
    ],
};
