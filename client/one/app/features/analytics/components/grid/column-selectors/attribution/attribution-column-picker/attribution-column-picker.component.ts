import './attribution-column-picker.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Input,
    Output,
    OnInit,
    OnDestroy,
} from '@angular/core';
import {ConversionWindowConfig} from '../../../../../../../core/conversion-pixels/types/conversion-windows-config';
import {PixelColumn} from '../../../../../types/pixel-column';
import * as pixelHelpers from './helpers/attribution-column-picker.helpers';
import * as arrayHelpers from '../../../../../../../shared/helpers/array.helpers';
import {downgradeComponent} from '@angular/upgrade/static';
import {AttributionColumnPickerStore} from './services/attribution-column-picker.store';
import PixelMetric from './types/pixel-metric';
import {merge, Observable, Subject} from 'rxjs';
import {takeUntil, map, distinctUntilChanged, tap} from 'rxjs/operators';
import {AuthStore} from '../../../../../../../core/auth/services/auth.store';
import {
    CONVERSION_PIXEL_CLICK_WINDOWS,
    CONVERSION_PIXEL_VIEW_WINDOWS,
} from '../../../../../../../core/conversion-pixels/conversion-pixels.config';

@Component({
    selector: 'zem-attribution-column-picker',
    templateUrl: './attribution-column-picker.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [AttributionColumnPickerStore],
})
export class AttributionColumnPickerComponent implements OnInit, OnDestroy {
    @Input()
    pixelColumns: PixelColumn[];
    @Output()
    toggleColumn = new EventEmitter<{field: string}>();
    @Output()
    toggleColumns = new EventEmitter<{fields: string[]}>();

    private ngUnsubscribe$: Subject<void> = new Subject();

    CLICK_CONVERSION_WINDOWS: ConversionWindowConfig[] = CONVERSION_PIXEL_CLICK_WINDOWS;
    VIEW_CONVERSION_WINDOWS: ConversionWindowConfig[] = CONVERSION_PIXEL_VIEW_WINDOWS;

    METRICS_OPTIONS_CLICK: PixelMetric[] = [
        {attribution: 'Click attribution', performance: 'Conversions'},
        {attribution: 'Click attribution', performance: 'Conversion rate'},
        {attribution: 'Click attribution', performance: 'CPA'},
    ];

    METRICS_OPTIONS_VIEW: PixelMetric[] = [];

    pixelsNames: string[];

    constructor(
        public store: AttributionColumnPickerStore,
        public authStore: AuthStore
    ) {}

    ngOnInit() {
        this.subscribeToStateUpdates();
        this.store.initStore(this.pixelColumns);
        const pixelsHaveRoas = this.pixelColumns[0].columns.some(
            column => column.data.performance === 'ROAS'
        );
        this.METRICS_OPTIONS_VIEW.push(
            {attribution: 'View attribution', performance: 'Conversions'},
            {
                attribution: 'View attribution',
                performance: 'Conversion rate',
            },
            {attribution: 'View attribution', performance: 'CPA'}
        );
        if (pixelsHaveRoas) {
            this.METRICS_OPTIONS_CLICK.push({
                attribution: 'Click attribution',
                performance: 'ROAS',
            });
            this.METRICS_OPTIONS_VIEW.push({
                attribution: 'View attribution',
                performance: 'ROAS',
            });
        }
    }

    onPixelChange(pixelsNames: string[]) {
        const pixels = this.pixelColumns.filter((pixel: PixelColumn) =>
            pixelsNames.some(name => name === pixel.name)
        );
        const pixelsToToggle = pixels
            .filter(pixel => !this.store.state.pixels.includes(pixel))
            .concat(
                this.store.state.pixels.filter(pixel => !pixels.includes(pixel))
            );
        const fieldsToToggle = pixelHelpers.getAllFields(
            pixelsToToggle,
            [this.store.state.clickConversionWindow],
            [this.store.state.viewConversionWindow],
            this.store.state.metrics
        );
        this.store.setPixels(pixels);
        if (!arrayHelpers.isEmpty(fieldsToToggle)) {
            this.toggleColumns.emit({
                fields: fieldsToToggle,
            });
        }
    }

    onMetricToggle($event: boolean, metric: PixelMetric) {
        const fieldsToToggle = pixelHelpers.getAllFields(
            this.store.state.pixels,
            [this.store.state.clickConversionWindow],
            [this.store.state.viewConversionWindow],
            [metric]
        );
        if ($event) {
            this.store.addMetric(metric);
        } else {
            this.store.removeMetric(metric);
        }
        if (!arrayHelpers.isEmpty(fieldsToToggle)) {
            this.toggleColumns.emit({
                fields: fieldsToToggle,
            });
        }
    }

    onClickConversionWindowChange(window: ConversionWindowConfig) {
        const fieldsToToggle = pixelHelpers.getAllFields(
            this.store.state.pixels,
            [this.store.state.clickConversionWindow, window],
            [],
            this.store.state.metrics
        );
        this.store.setClickConversionWindow(window);
        if (!arrayHelpers.isEmpty(fieldsToToggle)) {
            this.toggleColumns.emit({
                fields: fieldsToToggle,
            });
        }
    }

    onViewConversionWindowChange(window: ConversionWindowConfig) {
        const fieldsToToggle = pixelHelpers.getAllFields(
            this.store.state.pixels,
            [],
            [this.store.state.viewConversionWindow, window],
            this.store.state.metrics
        );
        this.store.setViewConversionWindow(window);
        if (!arrayHelpers.isEmpty(fieldsToToggle)) {
            this.toggleColumns.emit({
                fields: fieldsToToggle,
            });
        }
    }

    isMetricsSelected(option: PixelMetric): boolean {
        for (const metric of this.store.state.metrics) {
            if (
                option.attribution === metric.attribution &&
                option.performance === metric.performance
            ) {
                return true;
            }
        }
        return false;
    }

    private subscribeToStateUpdates() {
        merge(this.createPixelsNamesUpdater$())
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe();
    }

    private createPixelsNamesUpdater$(): Observable<any> {
        return this.store.state$.pipe(
            map(state => state.pixels),
            distinctUntilChanged(),
            tap(pixels => {
                this.pixelsNames = pixels.map(
                    (pixel: PixelColumn) => pixel.name
                );
            })
        );
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemAttributionColumnPicker',
    downgradeComponent({
        component: AttributionColumnPickerComponent,
        inputs: ['pixelColumns'],
        outputs: ['toggleColumn', 'toggleColumns'],
        propagateDigest: false,
    })
);
