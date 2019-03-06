import './integer-input.component.less';

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
import * as stringHelpers from '../../helpers/string.helpers';
import {KeyCode} from '../../../app.constants';

@Component({
    selector: 'zem-integer-input',
    templateUrl: './integer-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IntegerInputComponent implements OnInit, OnChanges {
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
    @Output()
    valueChange = new EventEmitter<string>();
    @Output()
    inputBlur = new EventEmitter<string>();

    keyFilter: number[];
    model: string;

    private regExp: RegExp;

    ngOnInit() {
        this.keyFilter = [KeyCode.ENTER];
        this.regExp = new RegExp('^\\d+$');
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;
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

    onModelChange($event: string) {
        this.valueChange.emit($event);
    }

    onBlur() {
        if (this.model !== this.value) {
            this.inputBlur.emit(this.model);
        }
    }

    private validate(
        currentValue: string,
        indexToInsert: number,
        valueToInsert: string
    ): boolean {
        const value = stringHelpers.insertStringAtIndex(
            currentValue,
            indexToInsert,
            valueToInsert
        );
        return this.regExp.test(value);
    }
}
