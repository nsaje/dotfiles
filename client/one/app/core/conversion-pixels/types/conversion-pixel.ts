import {ConversionWindowConfig} from './conversion-windows-config';

export interface ConversionPixel {
    id: string;
    accountId: string;
    name: string;
    archived?: boolean;
    url: string;
    redirectUrl?: string;
    notes?: string;
    lastTriggered: Date;
    impressions: number;
    conversionWindows: ConversionWindowConfig[];
}
