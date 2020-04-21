import {Injectable} from '@angular/core';
import {Store} from 'rxjs-observable-store';
import {AttributionColumnPickerStoreState} from './attribution-column-picker.store.state';
import {PixelColumn} from '../../../../../../types/pixel-column';
import {ConversionWindowConfig} from '../../../../../../../../core/conversion-pixels/types/conversion-windows-config';
import {
    VIEW_CONVERSION_WINDOWS,
    CLICK_CONVERSION_WINDOWS,
} from '../attribution-column-picker.config';
import * as pixelHelpers from '../helpers/attribution-column-picker.helpers';
import * as arrayHelpers from '../../../../../../../../shared/helpers/array.helpers';
import {PixelOptionsColumn} from '../../../../../../types/pixel-options-column';
import PixelMetric from '../types/pixel-metric';

@Injectable()
export class AttributionColumnPickerStore extends Store<
    AttributionColumnPickerStoreState
> {
    constructor() {
        super(new AttributionColumnPickerStoreState());
    }

    initStore(pixels: PixelColumn[]) {
        const preselectedPixels = this.getPreselectedPixels(pixels);
        const preselectedViewConversionWindow = this.getPreselectedViewConversionWindow(
            preselectedPixels
        );
        const preselectedClickConversionWindow = this.getPreselectedClickConversionWindow(
            preselectedPixels
        );
        const preselectedMetrics = this.getPreselectedMetrics(
            preselectedPixels
        );
        this.setState({
            ...this.state,
            pixels: preselectedPixels,
            viewConversionWindow: preselectedViewConversionWindow,
            clickConversionWindow: preselectedClickConversionWindow,
            metrics: preselectedMetrics,
        });
    }

    setPixels(pixels: PixelColumn[]) {
        this.patchState(pixels, 'pixels');
    }

    setClickConversionWindow(selectedWindow: ConversionWindowConfig) {
        this.patchState(selectedWindow, 'clickConversionWindow');
    }

    setViewConversionWindow(selectedWindow: ConversionWindowConfig) {
        this.patchState(selectedWindow, 'viewConversionWindow');
    }

    addMetric(metric: PixelMetric) {
        this.patchState([...this.state.metrics, metric], 'metrics');
    }

    removeMetric(metric: PixelMetric) {
        const metrics = this.state.metrics.filter(m => {
            return !(
                m.attribution === metric.attribution &&
                m.performance === metric.performance
            );
        });
        this.patchState(metrics, 'metrics');
    }

    private getPreselectedPixels(pixels: PixelColumn[]): PixelColumn[] {
        const selectedPixels = [];
        for (const pixel of pixels) {
            const selectedColumns: PixelOptionsColumn[] = pixel.columns.filter(
                (column: PixelOptionsColumn) => {
                    return column.visible === true;
                }
            );
            if (!arrayHelpers.isEmpty(selectedColumns)) {
                selectedPixels.push(pixel);
            }
        }
        return selectedPixels;
    }

    private getPreselectedClickConversionWindow(
        pixels: PixelColumn[]
    ): ConversionWindowConfig {
        if (!arrayHelpers.isEmpty(pixels)) {
            for (const column of pixels[0].columns) {
                if (
                    column.visible &&
                    column.data.attribution === 'Click attribution'
                ) {
                    return CLICK_CONVERSION_WINDOWS.find(
                        (window: ConversionWindowConfig) => {
                            return (
                                column.data.window ===
                                pixelHelpers.mapConversionWindowValue(
                                    window.value
                                )
                            );
                        }
                    );
                }
            }
        }
        return CLICK_CONVERSION_WINDOWS[0];
    }

    private getPreselectedViewConversionWindow(
        pixels: PixelColumn[]
    ): ConversionWindowConfig {
        if (!arrayHelpers.isEmpty(pixels)) {
            for (const column of pixels[0].columns) {
                if (
                    column.visible &&
                    column.data.attribution === 'View attribution'
                ) {
                    return VIEW_CONVERSION_WINDOWS.find(
                        (window: ConversionWindowConfig) => {
                            return (
                                column.data.window ===
                                pixelHelpers.mapConversionWindowValue(
                                    window.value
                                )
                            );
                        }
                    );
                }
            }
        }
        return VIEW_CONVERSION_WINDOWS[0];
    }

    private getPreselectedMetrics(pixels: PixelColumn[]): PixelMetric[] {
        const preselectedMetrics: PixelMetric[] = [];
        if (!arrayHelpers.isEmpty(pixels)) {
            for (const column of pixels[0].columns) {
                if (column.visible === true) {
                    preselectedMetrics.push({
                        attribution: column.data.attribution,
                        performance: column.data.performance,
                    });
                }
            }
        }
        return preselectedMetrics;
    }
}
