import {ConversionWindow} from '../../../../app.constants';
import {ConversionWindowConfig} from '../../../../core/conversion-pixels/types/conversion-windows-config';
import {CONVERSION_WINDOWS} from '../../../../app.config';

export const CLICK_CONVERSION_WINDOWS: ConversionWindowConfig[] = CONVERSION_WINDOWS;

export const VIEW_CONVERSION_WINDOWS: ConversionWindowConfig[] = [
    {name: '1 day', value: ConversionWindow.LEQ_1_DAY},
];
