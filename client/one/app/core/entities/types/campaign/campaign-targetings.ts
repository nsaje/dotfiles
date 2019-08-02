import {IncludedExcluded} from '../common/included-excluded';

export interface CampaignTargetings {
    publisherGroups?: IncludedExcluded<number[]>;
}
