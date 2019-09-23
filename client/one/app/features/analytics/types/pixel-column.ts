import {PixelOptionsColumn} from './pixel-options-column';

export interface PixelColumn {
    name: string;
    description?: string;
    columns: PixelOptionsColumn[];
}
