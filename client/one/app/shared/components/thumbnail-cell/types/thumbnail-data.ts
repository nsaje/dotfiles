import {AdType} from '../../../../app.constants';

export interface ThumbnailData {
    type: AdType;
    url: string;
    title: string | null;
    displayUrl: string;
    brandName: string | null;
    description: string | null;
    callToAction: string | null;
    displayHostedImageUrl: string | null;
    hostedImageUrl: string | null;
    landscapeHostedImageUrl: string | null;
    portraitHostedImageUrl: string | null;
    hostedIconUrl: string | null;
    imageWidth: string | null;
    imageHeight: string | null;
    adTag: string | null;
}
