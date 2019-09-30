import {AdGroup} from '../core/entities/types/ad-group/ad-group';
import {AdGroupExtras} from '../core/entities/types/ad-group/ad-group-extras';
import {adGroupMock} from './mocked-data/ad-group.mock';
import {adGroupExtrasMock} from './mocked-data/ad-group-extras.mock';
import {Campaign} from '../core/entities/types/campaign/campaign';
import {CampaignExtras} from '../core/entities/types/campaign/campaign-extras';
import {campaignMock} from './mocked-data/campaign.mock';
import {campaignExtrasMock} from './mocked-data/campaign-extras.mock';
import {Account} from '../core/entities/types/account/account';
import {AccountExtras} from '../core/entities/types/account/account-extras';
import {accountMock} from './mocked-data/account.mock';
import {accountExtrasMock} from './mocked-data/account-extras.mock';
import {Deal} from '../core/deals/types/deal';
import {dealMock} from './mocked-data/deal.mock';

export function getMockedAdGroup(): AdGroup {
    return adGroupMock;
}

export function getMockedAdGroupExtras(): AdGroupExtras {
    return adGroupExtrasMock;
}

export function getMockedCampaign(): Campaign {
    return campaignMock;
}

export function getMockedCampaignExtras(): CampaignExtras {
    return campaignExtrasMock;
}

export function getMockedAccount(): Account {
    return accountMock;
}

export function getMockedAccountExtras(): AccountExtras {
    return accountExtrasMock;
}

export function getMockedDeal(): Deal {
    return dealMock;
}
