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
    title: string;
    displayUrl: string;
    brandName: string;
    description: string;
    callToAction: string;
    tags: string[];
    imageUrl: string;
    iconUrl: string;
    adTag: string;
    videoAssetId: string;
    trackers: Tracker[];
}
