import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {AttributionColumnPickerComponent} from './attribution-column-picker.component';
import {AttributionLoockbackWindowPickerComponent} from '../attribution-lookback-window-picker/attribution-lookback-window-picker.component';
import {PixelColumn} from '../../types/pixel-column';
import {ConversionWindow} from '../../../../app.constants';

describe('AttributionColumnPickerComponent', () => {
    let component: AttributionColumnPickerComponent;
    let fixture: ComponentFixture<AttributionColumnPickerComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                AttributionColumnPickerComponent,
                AttributionLoockbackWindowPickerComponent,
            ],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(AttributionColumnPickerComponent);
        component = fixture.componentInstance;
    });

    const mockedPixelColumnsWithVisible: PixelColumn[] = [
        {
            columns: [
                {
                    data: {
                        attribution: '',
                        field: 'pixel_295_24',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / Click attribution',
                        pixel: 'pixel_295',
                        window: 24,
                    },
                    field: 'pixel_295_24',
                    type: 'number',
                    visible: false,
                },
                {
                    data: {
                        attribution: '',
                        field: 'avg_etfm_cost_per_pixel_295_24',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_295',
                        window: 24,
                    },
                    field: 'avg_etfm_cost_per_pixel_295_24',
                    type: 'currency',
                    visible: false,
                },
                {
                    data: {
                        attribution: '',
                        field: 'pixel_295_168',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / Click attribution',
                        pixel: 'pixel_295',
                        window: 168,
                    },
                    field: 'pixel_295_168',
                    type: 'number',
                    visible: false,
                },
                {
                    data: {
                        attribution: '_view',
                        field: 'pixel_295_24_view',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / View attribution',
                        pixel: 'pixel_295',
                        window: 24,
                    },
                    field: 'pixel_295_24_view',
                    type: 'number',
                    visible: false,
                },
            ],
            description: undefined,
            name: 'Book Sale',
        },
        {
            columns: [
                {
                    data: {
                        attribution: '',
                        field: 'avg_etfm_cost_per_pixel_4927_168',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_4927',
                        window: 168,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_168',
                    type: 'currency',
                    visible: false,
                },
                {
                    data: {
                        attribution: '',
                        field: 'pixel_4927_720',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / Click attribution',
                        pixel: 'pixel_4927',
                        window: 720,
                    },
                    field: 'pixel_4927_720',
                    type: 'number',
                    visible: false,
                },
                {
                    data: {
                        attribution: '',
                        field: 'avg_etfm_cost_per_pixel_4927_720',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_4927',
                        window: 720,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_720',
                    type: 'currency',
                    visible: true,
                },
                {
                    data: {
                        attribution: '_view',
                        field: 'pixel_4927_24_view',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / View attribution',
                        pixel: 'pixel_4927',
                        window: 24,
                    },
                    field: 'pixel_4927_24_view',
                    type: 'number',
                    visible: true,
                },
                {
                    data: {
                        attribution: '_view',
                        field: 'avg_etfm_cost_per_pixel_4927_24_view',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / View attribution',
                        pixel: 'pixel_4927',
                        window: 24,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_24_view',
                    type: 'currency',
                    visible: false,
                },
            ],
            description: undefined,
            name: 'BOR Nicole',
        },
    ];
    const mockedPixelColumnsWithoutVisible: PixelColumn[] = [
        {
            columns: [
                {
                    data: {
                        attribution: '',
                        field: 'pixel_295_24',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / Click attribution',
                        pixel: 'pixel_295',
                        window: 24,
                    },
                    field: 'pixel_295_24',
                    type: 'number',
                    visible: false,
                },
                {
                    data: {
                        attribution: '',
                        field: 'avg_etfm_cost_per_pixel_295_24',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_295',
                        window: 24,
                    },
                    field: 'avg_etfm_cost_per_pixel_295_24',
                    type: 'currency',
                    visible: false,
                },
                {
                    data: {
                        attribution: '',
                        field: 'pixel_295_168',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / Click attribution',
                        pixel: 'pixel_295',
                        window: 168,
                    },
                    field: 'pixel_295_168',
                    type: 'number',
                    visible: false,
                },
                {
                    data: {
                        attribution: '_view',
                        field: 'pixel_295_24_view',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / View attribution',
                        pixel: 'pixel_295',
                        window: 24,
                    },
                    field: 'pixel_295_24_view',
                    type: 'number',
                    visible: false,
                },
            ],
            description: undefined,
            name: 'Book Sale',
        },
        {
            columns: [
                {
                    data: {
                        attribution: '',
                        field: 'avg_etfm_cost_per_pixel_4927_168',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_4927',
                        window: 168,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_168',
                    type: 'currency',
                    visible: false,
                },
                {
                    data: {
                        attribution: '',
                        field: 'pixel_4927_720',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / Click attribution',
                        pixel: 'pixel_4927',
                        window: 720,
                    },
                    field: 'pixel_4927_720',
                    type: 'number',
                    visible: false,
                },
                {
                    data: {
                        attribution: '',
                        field: 'avg_etfm_cost_per_pixel_4927_720',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_4927',
                        window: 720,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_720',
                    type: 'currency',
                    visible: false,
                },
                {
                    data: {
                        attribution: '_view',
                        field: 'pixel_4927_24_view',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / View attribution',
                        pixel: 'pixel_4927',
                        window: 24,
                    },
                    field: 'pixel_4927_24_view',
                    type: 'number',
                    visible: false,
                },
                {
                    data: {
                        attribution: '_view',
                        field: 'avg_etfm_cost_per_pixel_4927_24_view',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / View attribution',
                        pixel: 'pixel_4927',
                        window: 24,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_24_view',
                    type: 'currency',
                    visible: false,
                },
            ],
            description: undefined,
            name: 'BOR Nicole',
        },
    ];

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly set selectedColumns', () => {
        component.pixelColumns = mockedPixelColumnsWithVisible;
        component.ngOnInit();
        component.ngOnChanges();
        expect(component.selectedColumns).toEqual([
            {
                data: {
                    attribution: '',
                    field: 'avg_etfm_cost_per_pixel_4927_720',
                    help: 'Average cost per acquisition.',
                    name: 'CPA / Click attribution',
                    pixel: 'pixel_4927',
                    window: 720,
                },
                field: 'avg_etfm_cost_per_pixel_4927_720',
                type: 'currency',
                visible: true,
            },
            {
                data: {
                    attribution: '_view',
                    field: 'pixel_4927_24_view',
                    help: 'Number of completions of the conversion goal',
                    name: 'Conversions / View attribution',
                    pixel: 'pixel_4927',
                    window: 24,
                },
                field: 'pixel_4927_24_view',
                type: 'number',
                visible: true,
            },
        ]);
    });

    it('should correclty set empty selectedColumns', () => {
        component.pixelColumns = mockedPixelColumnsWithoutVisible;
        component.ngOnInit();
        expect(component.selectedColumns).toEqual([]);
    });

    it('should correctly set selectedViewConversionWindow', () => {
        component.pixelColumns = mockedPixelColumnsWithVisible;
        component.ngOnInit();
        expect(component.selectedViewConversionWindow).toEqual({
            name: '1 day',
            value: ConversionWindow.LEQ_1_DAY,
        });
    });

    it('should correctly set default selectedViewConversionWindow', () => {
        component.pixelColumns = mockedPixelColumnsWithoutVisible;
        component.ngOnInit();
        expect(component.selectedViewConversionWindow).toEqual({
            name: '1 day',
            value: ConversionWindow.LEQ_1_DAY,
        });
    });

    it('should correctl set selectedClickConversionWindow', () => {
        component.pixelColumns = mockedPixelColumnsWithVisible;
        component.ngOnInit();
        expect(component.selectedClickConversionWindow).toEqual({
            name: '30 days',
            value: ConversionWindow.LEQ_30_DAYS,
        });
    });
    it('should correctly set default selectedClickConversionWindow', () => {
        component.pixelColumns = mockedPixelColumnsWithoutVisible;
        component.ngOnInit();
        expect(component.selectedClickConversionWindow).toEqual({
            name: '1 day',
            value: ConversionWindow.LEQ_1_DAY,
        });
    });

    it('should correctly set availableColumns', () => {
        component.pixelColumns = mockedPixelColumnsWithVisible;
        component.ngOnInit();
        expect(component.availableColumns).toEqual([
            {
                data: {
                    attribution: '',
                    field: 'pixel_4927_720',
                    help: 'Number of completions of the conversion goal',
                    name: 'Conversions / Click attribution',
                    pixel: 'pixel_4927',
                    window: 720,
                },
                field: 'pixel_4927_720',
                type: 'number',
                visible: false,
            },
            {
                data: {
                    attribution: '',
                    field: 'avg_etfm_cost_per_pixel_4927_720',
                    help: 'Average cost per acquisition.',
                    name: 'CPA / Click attribution',
                    pixel: 'pixel_4927',
                    window: 720,
                },
                field: 'avg_etfm_cost_per_pixel_4927_720',
                type: 'currency',
                visible: true,
            },
            {
                data: {
                    attribution: '_view',
                    field: 'pixel_4927_24_view',
                    help: 'Number of completions of the conversion goal',
                    name: 'Conversions / View attribution',
                    pixel: 'pixel_4927',
                    window: 24,
                },
                field: 'pixel_4927_24_view',
                type: 'number',
                visible: true,
            },
            {
                data: {
                    attribution: '_view',
                    field: 'avg_etfm_cost_per_pixel_4927_24_view',
                    help: 'Average cost per acquisition.',
                    name: 'CPA / View attribution',
                    pixel: 'pixel_4927',
                    window: 24,
                },
                field: 'avg_etfm_cost_per_pixel_4927_24_view',
                type: 'currency',
                visible: false,
            },
        ]);
    });

    it('should correctly set selectedPixel', () => {
        component.pixelColumns = mockedPixelColumnsWithVisible;
        component.ngOnInit();
        expect(component.selectedPixel).toEqual({
            columns: [
                {
                    data: {
                        attribution: '',
                        field: 'avg_etfm_cost_per_pixel_4927_168',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_4927',
                        window: 168,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_168',
                    type: 'currency',
                    visible: false,
                },
                {
                    data: {
                        attribution: '',
                        field: 'pixel_4927_720',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / Click attribution',
                        pixel: 'pixel_4927',
                        window: 720,
                    },
                    field: 'pixel_4927_720',
                    type: 'number',
                    visible: false,
                },
                {
                    data: {
                        attribution: '',
                        field: 'avg_etfm_cost_per_pixel_4927_720',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / Click attribution',
                        pixel: 'pixel_4927',
                        window: 720,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_720',
                    type: 'currency',
                    visible: true,
                },
                {
                    data: {
                        attribution: '_view',
                        field: 'pixel_4927_24_view',
                        help: 'Number of completions of the conversion goal',
                        name: 'Conversions / View attribution',
                        pixel: 'pixel_4927',
                        window: 24,
                    },
                    field: 'pixel_4927_24_view',
                    type: 'number',
                    visible: true,
                },
                {
                    data: {
                        attribution: '_view',
                        field: 'avg_etfm_cost_per_pixel_4927_24_view',
                        help: 'Average cost per acquisition.',
                        name: 'CPA / View attribution',
                        pixel: 'pixel_4927',
                        window: 24,
                    },
                    field: 'avg_etfm_cost_per_pixel_4927_24_view',
                    type: 'currency',
                    visible: false,
                },
            ],
            description: undefined,
            name: 'BOR Nicole',
        });
    });

    it('should correcty set first pixel selectedPixel as default if none is selected', () => {
        component.pixelColumns = mockedPixelColumnsWithoutVisible;
        component.ngOnInit();
        expect(component.selectedPixel).toEqual(
            mockedPixelColumnsWithoutVisible[0]
        );
    });
});
