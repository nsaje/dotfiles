import './date-setting.component.less';

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
    selector: 'zem-date-setting',
    templateUrl: './date-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DateSettingComponent implements OnChanges {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
    @Input()
    value: Date;
    @Input()
    allowManualOverride: boolean = false;
    @Input()
    minDate: Date;
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
                this.isManualOverrideEnabled = true;
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
