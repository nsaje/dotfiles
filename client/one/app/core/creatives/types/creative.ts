import {AdType} from '../../../app.constants';
import {Tracker} from './tracker';

export interface Creative {
    id: string;
    agencyId: string | null;
    agencyName: string | null;
    accountId: string | null;
    accountName: string | null;
    type: AdType;
    url: string;
    title: string | null;
    displayUrl: string;
    brandName: string | null;
    description: string | null;
    callToAction: string | null;
    tags: string[];
    displayHostedImageUrl: string | null;
    hostedImageUrl: string | null;
    landscapeHostedImageUrl: string | null;
    portraitHostedImageUrl: string | null;
    hostedIconUrl: string | null;
    imageWidth: string | null;
    imageHeight: string | null;
    adTag: string | null;
    videoAssetId: string | null;
    trackers: Tracker[];
}
