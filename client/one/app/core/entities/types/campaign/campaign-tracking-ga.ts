import {GaTrackingType} from '../../../../app.constants';

export interface CampaignTrackingGa {
    enabled?: boolean;
    type?: GaTrackingType;
    webPropertyId?: string;
}
