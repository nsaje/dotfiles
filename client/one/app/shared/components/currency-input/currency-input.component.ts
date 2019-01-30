import './currency-input.component.less';

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
import * as numericHelpers from '../../helpers/numeric.helpers';
import * as currencyHelpers from '../../helpers/currency.helpers';
import {KeyCode} from '../../../app.constants';

@Component({
    selector: 'zem-currency-input',
    templateUrl: './currency-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CurrencyInputComponent implements OnInit, OnChanges {
    @Input()
    value: string;
    @Input()
    placeholder: string;
    @Input()
    isDisabled: boolean;
    @Input()
    hasError: boolean;
    @Input()
    currencySymbol: string;
    @Input()
    fractionSize: number;
    @Output()
    valueChange = new EventEmitter<string>();

    keyFilter: number[];
    model: string;

    private regExp: RegExp;

    ngOnInit(): void {
        this.fractionSize = commonHelpers.getValueOrDefault(
            this.fractionSize,
            2
        );
        this.keyFilter = [KeyCode.ENTER, KeyCode.SPACE];
        this.regExp = new RegExp(`^\\d+(\\.\\d{0,${this.fractionSize}})?$`);
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = currencyHelpers.formatCurrency(
                this.value,
                this.fractionSize
            );
        }
    }

    onKeydown($event: KeyboardEvent) {
        const indexToInsert = Number((<any>$event.target).selectionStart);
        const valueToInsert = $event.key;
        const isValid = this.validate(this.model, indexToInsert, valueToInsert);
        if (!isValid) {
            // prevent the execution of $event
            // the ngModel will not be updated
            $event.preventDefault();
        }
    }

    onPaste($event: ClipboardEvent) {
        const indexToInsert = Number((<any>$event.target).selectionStart);
        const valueToInsert = $event.clipboardData.getData('text/plain');
        const isValid = this.validate(this.model, indexToInsert, valueToInsert);
        if (!isValid) {
            // prevent the execution of $event
            // the ngModel will not be updated
            $event.preventDefault();
        }
    }

    onFocus() {
        this.model = numericHelpers.parseDecimal(this.model, this.fractionSize);
    }

    onBlur() {
        const decimalValue = numericHelpers.parseDecimal(
            this.model,
            this.fractionSize
        );
        if (decimalValue !== this.value) {
            this.valueChange.emit(decimalValue);
        } else {
            this.model = currencyHelpers.formatCurrency(
                this.model,
                this.fractionSize
            );
        }
    }

    private validate(
        currentValue: string,
        indexToInsert: number,
        valueToInsert: string
    ): boolean {
        const value = commonHelpers.insertStringAtIndex(
            currentValue,
            indexToInsert,
            valueToInsert
        );
        return this.regExp.test(value);
    }
}
