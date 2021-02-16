import {AdType} from '../../../app.constants';
import {Tracker} from './tracker';

export interface CreativeCandidate {
    // AdTypeSerializer
    type?: AdType;
    // CreativeCandidateCommonSerializer
    id?: string;
    originalCreativeId?: string;
    url?: string;
    title?: string;
    displayUrl?: string;
    tags?: string[];
    trackers?: Tracker[];
    // NativeCreativeCandidateSerializer
    brandName?: string;
    description?: string;
    callToAction?: string;
    imageCrop?: string; // enum?
    // VideoCreativeCandidateSerializer
    videoAssetId?: string;
    // ImageCreativeCandidateSerializer (TODO?)
    imageUrl?: string;
    iconUrl?: string;
    // AdTagCreativeCandidateSerializer
    adTag?: string;
}
