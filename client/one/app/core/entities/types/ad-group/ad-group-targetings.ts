import {OperatingSystem} from '../common/operating-system';
import {Browser} from '../common/browser';
import {IncludedExcluded} from '../common/included-excluded';
import {TargetRegions} from '../common/target-regions';
import {InterestCategory} from 'one/app/app.constants';
import {TargetLanguage} from '../common/target-language';

export interface AdGroupTargetings {
    devices?: string[];
    placements?: string[];
    os?: OperatingSystem[];
    browsers?: Browser[];
    audience?: any;
    geo?: IncludedExcluded<TargetRegions>;
    interest?: IncludedExcluded<InterestCategory[]>;
    publisherGroups?: IncludedExcluded<number[]>;
    customAudiences?: IncludedExcluded<number[]>;
    retargetingAdGroups?: IncludedExcluded<number[]>;
    language?: TargetLanguage;
}
