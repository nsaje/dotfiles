import {AdGroup} from '../core/entities/types/ad-group/ad-group';
import {AdGroupExtras} from '../core/entities/types/ad-group/ad-group-extras';
import {adGroupMock} from './mocked-data/ad-group.mock';
import {adGroupExtrasMock} from './mocked-data/ad-group-extras.mock';
import {Campaign} from '../core/entities/types/campaign/campaign';
import {CampaignExtras} from '../core/entities/types/campaign/campaign-extras';
import {campaignMock} from './mocked-data/campaign.mock';
import {campaignExtrasMock} from './mocked-data/campaign-extras.mock';

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
