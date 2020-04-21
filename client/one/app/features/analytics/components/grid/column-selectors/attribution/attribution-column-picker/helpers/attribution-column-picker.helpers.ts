import {ConversionWindow} from '../../../../../../../../app.constants';
import {PixelColumn} from '../../../../../../types/pixel-column';
import {ConversionWindowConfig} from '../../../../../../../../core/conversion-pixels/types/conversion-windows-config';
import PixelMetric from '../types/pixel-metric';
import * as arrayHelpers from '../../../../../../../../shared/helpers/array.helpers';

export function mapConversionWindowValue(window: ConversionWindow): number {
    switch (window) {
        case ConversionWindow.LEQ_1_DAY:
            return 24;
        case ConversionWindow.LEQ_7_DAYS:
            return 168;
        case ConversionWindow.LEQ_30_DAYS:
            return 720;
    }
}

export function getAllFields(
    pixels: PixelColumn[],
    clickConversionWindow: ConversionWindowConfig[],
    viewConversionWindow: ConversionWindowConfig[],
    metrics: PixelMetric[]
): string[] {
    const fieldsToToggle: string[] = [];
    if (arrayHelpers.isEmpty(pixels) || arrayHelpers.isEmpty(metrics)) {
        return [];
    } else {
        for (const pixel of pixels) {
            for (const column of pixel.columns) {
                for (const metric of metrics) {
                    let conversionWindow: ConversionWindowConfig[] = [];
                    if (column.data.attribution === 'View attribution') {
                        conversionWindow = viewConversionWindow;
                    }
                    if (column.data.attribution === 'Click attribution') {
                        conversionWindow = clickConversionWindow;
                    }
                    for (const window of conversionWindow) {
                        if (
                            mapConversionWindowValue(window.value) ===
                                column.data.window &&
                            metric.attribution === column.data.attribution &&
                            metric.performance === column.data.performance
                        ) {
                            fieldsToToggle.push(column.field);
                        }
                    }
                }
            }
        }
    }
    return fieldsToToggle;
}
