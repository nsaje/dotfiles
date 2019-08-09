import {IncludedExcluded} from '../common/included-excluded';

export interface AccountTargeting {
    publisherGroups?: IncludedExcluded<number[]>;
}
