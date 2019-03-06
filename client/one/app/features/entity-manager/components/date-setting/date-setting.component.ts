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
    infoMessage: string;
    @Input()
    value: Date;
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

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;
        }
    }

    onValueChange($event: Date) {
        this.valueChange.emit($event);
    }
}
