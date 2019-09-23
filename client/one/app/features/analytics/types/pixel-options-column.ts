import {PixelData} from './pixel-data';

export interface PixelOptionsColumn {
    field: string;
    type: string;
    visible: boolean;
    data: PixelData;
}
