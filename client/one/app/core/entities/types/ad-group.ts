import {AdGroupState} from '../../../app.constants';

export interface AdGroup {
    id: number;
    state: AdGroupState;
    archived: boolean;
}
