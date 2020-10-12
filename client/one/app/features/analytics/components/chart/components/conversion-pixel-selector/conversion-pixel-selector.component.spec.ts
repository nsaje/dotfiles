import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ConversionPixelSelectorComponent} from './conversion-pixel-selector.component';
import {SharedModule} from '../../../../../../shared/shared.module';
import {ChartMetricData} from '../../types/chart-metric-data';
import {
    ConversionPixelAttribution,
    ConversionPixelKPI,
} from '../../../../../../core/conversion-pixels/conversion-pixel.constants';
import {SimpleChanges, SimpleChange} from '@angular/core';
import {ChartCategory} from '../../types/chart-category';
import {PixelOption} from './types/pixel-option';
import {CONVERSION_WINDOW_NUMBER_FORMAT} from '../../../../../../app.config';
import {ConversionWindow} from '../../../../../../app.constants';

describe('ConversionPixelSelectorComponent', () => {
    let component: ConversionPixelSelectorComponent;
    let fixture: ComponentFixture<ConversionPixelSelectorComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ConversionPixelSelectorComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ConversionPixelSelectorComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly set selected properties on selected metric input', () => {
        const pixelCategories = [
            {
                name: 'All Conversions',
                subcategories: [],
                metrics: [
                    {
                        attribution: 'CLICK',
                        internal: false,
                        name: 'All Conversions 1 day - Click attr.',
                        performance: 'CONVERSIONS',
                        pixel: 'All Conversions',
                        shown: true,
                        value: 'pixel_1394_24',
                        window: 24,
                    },

                    {
                        attribution: 'CLICK',
                        costMode: 'public',
                        fractionSize: 2,
                        internal: false,
                        name: 'CPA (All Conversions 1 day - Click attr.)',
                        performance: 'CPA',
                        pixel: 'All Conversions',
                        shown: true,
                        type: 'currency',
                        value: 'avg_etfm_cost_per_pixel_1394_24',
                        window: 24,
                    },

                    {
                        attribution: 'CLICK',
                        costMode: 'public',
                        fractionSize: 2,
                        internal: false,
                        name:
                            'Conversion rate (All Conversions 1 day - Click attr.)',
                        performance: 'CONVERSION_RATE',
                        pixel: 'All Conversions',
                        shown: true,
                        type: 'currency',
                        value: 'conversion_rate_per_pixel_1394_24',
                        window: 24,
                    },
                ],
            },
            {
                name: 'Book This Package',
                subcategories: [],
                metrics: [
                    {
                        attribution: 'CLICK',
                        internal: false,
                        name: 'Book This Package 1 day - Click attr.',
                        performance: 'CONVERSIONS',
                        pixel: 'Book This Package',
                        shown: true,
                        value: 'pixel_1353_24',
                        window: 24,
                    },

                    {
                        attribution: 'CLICK',
                        costMode: 'public',
                        fractionSize: 2,
                        internal: false,
                        name: 'CPA (Book This Package 1 day - Click attr.)',
                        performance: 'CPA',
                        pixel: 'Book This Package',
                        shown: true,
                        type: 'currency',
                        value: 'avg_etfm_cost_per_pixel_1353_24',
                        window: 24,
                    },
                ],
            },
        ] as ChartCategory[];

        const selectedMetric = {
            attribution: 'CLICK',
            costMode: 'public',
            fractionSize: 2,
            internal: false,
            name: 'CPA (All Conversions 1 day - Click attr.)',
            performance: 'CPA',
            pixel: 'All Conversions',
            shown: true,
            type: 'currency',
            value: 'avg_etfm_cost_per_pixel_1394_24',
            window: 24,
        } as ChartMetricData;

        component.pixelCategories = pixelCategories;
        component.selectedMetric = selectedMetric;

        expect(component.selectedPixel).toEqual(undefined);
        expect(component.selectedKPI).toEqual(undefined);
        expect(component.selectedOption).toEqual(undefined);

        let changes: SimpleChanges;
        changes = {
            selectedMetric: new SimpleChange(
                null,
                component.selectedMetric,
                false
            ),
        };
        component.ngOnChanges(changes);

        expect(component.selectedMetric).toEqual(selectedMetric);
        expect(component.selectedPixel).toEqual(pixelCategories[0]);
        expect(component.selectedKPI).toEqual(ConversionPixelKPI.CPA);
        expect(component.selectedOption).toEqual({
            name: '1 day click attribution',
            attribution: ConversionPixelAttribution.CLICK,
            window: CONVERSION_WINDOW_NUMBER_FORMAT[ConversionWindow.LEQ_1_DAY],
        } as PixelOption);
    });

    it('should not set selected properties when selected metric input is not pixel', () => {
        const pixelCategories = [
            {
                name: 'All Conversions',
                subcategories: [],
                metrics: [
                    {
                        attribution: 'CLICK',
                        internal: false,
                        name: 'All Conversions 1 day - Click attr.',
                        performance: 'CONVERSIONS',
                        pixel: 'All Conversions',
                        shown: true,
                        value: 'pixel_1394_24',
                        window: 24,
                    },

                    {
                        attribution: 'CLICK',
                        costMode: 'public',
                        fractionSize: 2,
                        internal: false,
                        name: 'CPA (All Conversions 1 day - Click attr.)',
                        performance: 'CPA',
                        pixel: 'All Conversions',
                        shown: true,
                        type: 'currency',
                        value: 'avg_etfm_cost_per_pixel_1394_24',
                        window: 24,
                    },

                    {
                        attribution: 'CLICK',
                        costMode: 'public',
                        fractionSize: 2,
                        internal: false,
                        name:
                            'Conversion rate (All Conversions 1 day - Click attr.)',
                        performance: 'CONVERSION_RATE',
                        pixel: 'All Conversions',
                        shown: true,
                        type: 'currency',
                        value: 'conversion_rate_per_pixel_1394_24',
                        window: 24,
                    },
                ],
            },
        ] as ChartCategory[];

        const selectedMetric = {
            internal: false,
            name: 'Impressions',
            shown: true,
            type: 'number',
            value: 'impressions',
        } as ChartMetricData;

        component.pixelCategories = pixelCategories;
        component.selectedMetric = selectedMetric;

        expect(component.selectedPixel).toEqual(undefined);
        expect(component.selectedKPI).toEqual(undefined);
        expect(component.selectedOption).toEqual(undefined);

        let changes: SimpleChanges;
        changes = {
            selectedMetric: new SimpleChange(
                null,
                component.selectedMetric,
                false
            ),
        };
        component.ngOnChanges(changes);

        expect(component.selectedMetric).toEqual(selectedMetric);
        expect(component.selectedPixel).toEqual(undefined);
        expect(component.selectedKPI).toEqual(undefined);
        expect(component.selectedOption).toEqual(undefined);
    });
});
