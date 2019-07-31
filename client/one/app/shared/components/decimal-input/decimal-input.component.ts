import './decimal-input.component.less';

import {
    Component,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    EventEmitter,
    Output,
    Input,
    OnInit,
} from '@angular/core';
import * as commonHelpers from '../../helpers/common.helpers';
import * as stringHelpers from '../../helpers/string.helpers';
import * as numericHelpers from '../../helpers/numeric.helpers';

@Component({
    selector: 'zem-decimal-input',
    templateUrl: './decimal-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DecimalInputComponent implements OnInit, OnChanges {
    @Input()
    value: string;
    @Input()
    placeholder: string;
    @Input()
    isDisabled: boolean = false;
    @Input()
    isFocused: boolean = false;
    @Input()
    hasError: boolean = false;
    @Input()
    fractionSize: number;
    @Input()
    minValue: number;
    @Input()
    maxValue: number;
    @Output()
    valueChange = new EventEmitter<string>();
    @Output()
    inputBlur = new EventEmitter<string>();
    @Output()
    inputKeydown = new EventEmitter<KeyboardEvent>();

    model: string;

    private regExp: RegExp;

    ngOnInit() {
        this.fractionSize = commonHelpers.getValueOrDefault(
            this.fractionSize,
            2
        );
        this.regExp = new RegExp(
            `^[-+]?(\\d+(\\.\\d{0,${this.fractionSize}})?)?$`
        );
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = numericHelpers.parseDecimal(
                this.value,
                this.fractionSize
            );
        }
    }

    onKeydown($event: KeyboardEvent) {
        this.inputKeydown.emit($event);
        const indexToInsert = Number((<any>$event.target).selectionStart);
        const valueToInsert = $event.key;
        const isValid = this.validate(
            this.model,
            indexToInsert,
            valueToInsert,
            this.minValue,
            this.maxValue
        );
        if (!isValid) {
            // prevent the execution of $event
            // the ngModel will not be updated
            $event.preventDefault();
        }
    }

    onPaste($event: ClipboardEvent) {
        const indexToInsert = Number((<any>$event.target).selectionStart);
        const valueToInsert = $event.clipboardData.getData('text/plain');
        const isValid = this.validate(
            this.model,
            indexToInsert,
            valueToInsert,
            this.minValue,
            this.maxValue
        );
        if (!isValid) {
            // prevent the execution of $event
            // the ngModel will not be updated
            $event.preventDefault();
        }
    }

    onModelChange($event: string) {
        this.valueChange.emit($event);
    }

    onBlur() {
        const decimalValue = numericHelpers.parseDecimal(
            this.model,
            this.fractionSize
        );
        if (decimalValue !== this.value) {
            this.inputBlur.emit(decimalValue);
        } else {
            this.model = decimalValue;
        }
    }

    private validate(
        currentValue: string,
        indexToInsert: number,
        valueToInsert: string,
        minValue: number,
        maxValue: number
    ): boolean {
        const value = stringHelpers.insertStringAtIndex(
            currentValue,
            indexToInsert,
            valueToInsert
        );
        if (!this.regExp.test(value)) {
            return false;
        }
        return numericHelpers.validateMinMax(
            parseFloat(value),
            minValue,
            maxValue
        );
    }
}
