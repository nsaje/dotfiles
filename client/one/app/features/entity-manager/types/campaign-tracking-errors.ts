import {FieldErrors} from '../../../shared/types/field-errors';
import {CampaignTrackingGaErrors} from './campaign-tracking-ga-errors';
import {CampaignTrackingAdobeErrors} from './campaign-tracking-adobe-errors';

export interface CampaignTrackingErrors {
    ga?: CampaignTrackingGaErrors;
    adobe?: CampaignTrackingAdobeErrors;
}
