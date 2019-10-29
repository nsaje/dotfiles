import './date-form-group.component.less';

import {
    Component,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';

@Component({
    selector: 'zem-date-form-group',
    templateUrl: './date-form-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DateFormGroupComponent implements OnChanges {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
    @Input()
    value: Date;
    @Input()
    allowManualOverride: boolean = false;
    @Input()
    manualOverrideLabel: string;
    @Input()
    minDate: Date;
    @Input()
    maxDate: Date;
    @Input()
    appendTo: 'body';
    @Input()
    isDisabled: boolean = false;
    @Input()
    isFocused: boolean = false;
    @Input()
    errors: string[];
    @Output()
    valueChange = new EventEmitter<Date>();

    model: Date;
    lastNonNullValue: Date;
    isManualOverrideEnabled: boolean;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;

            if (this.model) {
                this.lastNonNullValue = this.model;
                this.isManualOverrideEnabled = false;
            } else {
                this.isManualOverrideEnabled = this.allowManualOverride;
            }
        }
    }

    onValueChange($event: Date) {
        this.valueChange.emit($event);
    }

    onManualOverrideToggle($event: boolean) {
        if ($event) {
            this.valueChange.emit(null);
        } else {
            this.valueChange.emit(
                this.lastNonNullValue || this.minDate || new Date()
            );
        }
    }
}
