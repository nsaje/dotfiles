import {PixelColumn} from '../../../types/pixel-column';
import {ConversionWindowConfig} from '../../../../../core/conversion-pixels/types/conversion-windows-config';
import PixelMetric from '../types/pixel-metric';

export class AttributionColumnPickerStoreState {
    pixels: PixelColumn[] = [];
    clickConversionWindow: ConversionWindowConfig = {
        name: null,
        value: null,
    };
    viewConversionWindow: ConversionWindowConfig = {
        name: null,
        value: null,
    };
    metrics: PixelMetric[] = [];
}
