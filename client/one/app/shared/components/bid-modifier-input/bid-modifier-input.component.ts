import './bid-modifier-input.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnChanges,
    SimpleChanges,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import * as numericHelpers from '../../helpers/numeric.helpers';

@Component({
    selector: 'zem-bid-modifier-input',
    templateUrl: './bid-modifier-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BidModifierInputComponent implements OnChanges {
    @Input()
    value: string;
    @Input()
    fractionSize: number;
    @Input()
    minValue: number;
    @Input()
    maxValue: number;
    @Input()
    isFocused: boolean = false;
    @Output()
    valueChange = new EventEmitter<string>();
    @Output()
    inputKeydown = new EventEmitter<KeyboardEvent>();

    model: string;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.value) {
            this.model = this.value;
        }
    }

    onValueChange($event: string) {
        this.valueChange.emit($event);
    }

    onInputBlur($event: string) {
        this.valueChange.emit($event);
    }

    onInputKeydown($event: KeyboardEvent) {
        this.inputKeydown.emit($event);
    }

    addDeltaPercent(deltaPercent: number): void {
        let value = parseFloat(this.model);
        if (isNaN(value)) {
            value = 0.0;
        }
        const newValue = value + deltaPercent;
        const isValid = numericHelpers.validateMinMax(
            newValue,
            this.minValue,
            this.maxValue
        );
        if (isValid) {
            this.valueChange.emit(newValue.toFixed(2));
        }
    }
}
