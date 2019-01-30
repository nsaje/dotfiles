import './text-setting.component.less';

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
    selector: 'zem-text-setting',
    templateUrl: './text-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TextSettingComponent implements OnChanges {
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
    maxLength: number;
    @Input()
    isDisabled: boolean;
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

    onBlur($event: FocusEvent) {
        if (this.model !== this.value) {
            this.valueChange.emit(this.model);
        }
    }
}
