import './checkbox-setting.component.less';

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
    selector: 'zem-checkbox-setting',
    templateUrl: './checkbox-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CheckboxSettingComponent implements OnChanges {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
    @Input()
    value: boolean;
    @Input()
    isDisabled: boolean = false;
    @Input()
    errors: string[];
    @Output()
    valueChange = new EventEmitter<boolean>();

    model: boolean;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;
        }
    }

    onToggle($event: boolean) {
        this.valueChange.emit($event);
    }
}
