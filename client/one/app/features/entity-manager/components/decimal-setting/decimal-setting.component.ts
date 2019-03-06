import './decimal-setting.component.less';

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
    selector: 'zem-decimal-setting',
    templateUrl: './decimal-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DecimalSettingComponent implements OnChanges {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
    @Input()
    infoMessage: string;
    @Input()
    value: string;
    @Input()
    placeholder: string;
    @Input()
    isDisabled: boolean;
    @Input()
    fractionSize: number;
    @Input()
    errors: string[];
    @Output()
    valueChange = new EventEmitter<string>();

    model: string;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;
        }
    }

    onInputBlur($event: string) {
        this.valueChange.emit($event);
    }
}
