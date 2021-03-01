import {FunnelStep} from '../bid-insights.constants';
import {AdGroupInfoSection} from './ad-group-info-section';

export interface AdGroupInfo {
    [FunnelStep.TARGETING]: AdGroupInfoSection[];
    [FunnelStep.BUDGET]: AdGroupInfoSection[];
    [FunnelStep.EXTERNAL_BLOCKS]: AdGroupInfoSection[];
    [FunnelStep.INTERNAL_AUCTION]: AdGroupInfoSection[];
}
