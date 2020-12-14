import './decimal-input.component.less';

import {
    Component,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    EventEmitter,
    Output,
    Input,
    ChangeDetectorRef,
    OnInit,
} from '@angular/core';
import * as numericHelpers from '../../helpers/numeric.helpers';
import {parseDecimal} from '../../helpers/numeric.helpers';
import {getValueOrDefault} from '../../helpers/common.helpers';
import {simulateTextChange} from '../../helpers/text-input.helpers';

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

    private validInputRegex: RegExp;
    private inputValidators: ((value: string) => boolean)[] = [
        this.validateRegex.bind(this),
        this.validateMinMax.bind(this),
    ];
    private isModelLocked: boolean = false;
    private isModelChanged: boolean = false;

    constructor(private changeDetectorRef: ChangeDetectorRef) {}

    ngOnInit(): void {
        this.fractionSize = getValueOrDefault(this.fractionSize, 2);
        this.validInputRegex = new RegExp(
            `^[-+]?((\\d+)?(\\.\\d{0,${this.fractionSize}})?)?$`
        );
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value && !this.isModelLocked) {
            this.model = this.formatModel(this.value);
        }
    }

    onFocus() {
        this.isModelChanged = false;
    }

    onKeydown($event: KeyboardEvent) {
        this.inputKeydown.emit($event);
        this.processInputEvent($event);
    }

    onPaste($event: ClipboardEvent) {
        this.processInputEvent($event);
    }

    onBlur() {
        if (!this.isModelChanged) {
            return;
        }

        const formattedModel: string = this.formatModel(this.model);

        if (this.isInputValid(formattedModel)) {
            this.inputBlur.emit(formattedModel);
            this.model = formattedModel;
        }
    }

    onModelChange() {
        if (this.isModelLocked) {
            this.isModelLocked = false;
        } else {
            this.undoModelChange();
        }
    }

    private formatModel(text: string) {
        return parseDecimal(text, this.fractionSize);
    }

    private processInputEvent($event: KeyboardEvent | ClipboardEvent) {
        const nextModel: string = simulateTextChange(this.model, $event);

        if (this.isInputValid(nextModel)) {
            this.isModelLocked = true;
            this.isModelChanged = true;
            const formattedModel: string = this.formatModel(nextModel);
            this.valueChange.emit(formattedModel);
        } else {
            $event.preventDefault();
        }
    }

    private undoModelChange() {
        setTimeout(() => {
            this.model = this.formatModel(this.value);
            this.changeDetectorRef.detectChanges();
        });
    }

    private isInputValid(value: string): boolean {
        return this.inputValidators
            .map(v => v(value))
            .reduce((a, b) => a && b, true);
    }

    private validateRegex(value: string): boolean {
        return this.validInputRegex.test(value);
    }

    private validateMinMax(value: string): boolean {
        return numericHelpers.validateMinMax(
            parseFloat(value),
            this.minValue,
            this.maxValue
        );
    }
}
