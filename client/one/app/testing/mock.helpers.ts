import {AdGroup} from '../core/entities/types/ad-group/ad-group';
import {AdGroupExtras} from '../core/entities/types/ad-group/ad-group-extras';
import {adGroupMock} from './mocked-data/ad-group.mock';
import {adGroupExtrasMock} from './mocked-data/ad-group-extras.mock';

export function getMockedAdGroup(): AdGroup {
    return adGroupMock;
}

export function getMockedAdGroupExtras(): AdGroupExtras {
    return adGroupExtrasMock;
}
