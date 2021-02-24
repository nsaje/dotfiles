import {AdGroupInfoStep} from '../bid-insights.constants';
import {AdGroupSectionInfo} from './ad-group-section-info';

export interface AdGroupInfo {
    [AdGroupInfoStep.TARGETING]: AdGroupSectionInfo[];
    [AdGroupInfoStep.BUDGET]: AdGroupSectionInfo[];
    [AdGroupInfoStep.EXTERNAL_BLOCKS]: AdGroupSectionInfo[];
    [AdGroupInfoStep.INTERNAL_AUCTION]: AdGroupSectionInfo[];
}
