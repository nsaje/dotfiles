import './attribution-lookback-window-picker.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Input,
    Output,
} from '@angular/core';
import {ConversionWindowConfig} from '../../../../../../../core/conversion-pixels/types/conversion-windows-config';
import {ConversionWindow} from '../../../../../../../app.constants';

@Component({
    selector: 'zem-attribution-lookback-window-picker',
    templateUrl: './attribution-lookback-window-picker.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AttributionLoockbackWindowPickerComponent {
    @Input()
    conversionWindows: ConversionWindowConfig[];
    @Input()
    selectedConversionWindow: ConversionWindowConfig;
    @Output()
    changeWindow = new EventEmitter<ConversionWindowConfig>();

    onConversionWindowChange($event: ConversionWindow) {
        this.selectedConversionWindow = this.conversionWindows.find(
            (window: ConversionWindowConfig) => {
                return window.value === $event;
            }
        );
    }

    selectClickConversionWindow() {
        this.changeWindow.emit(this.selectedConversionWindow);
    }
}
