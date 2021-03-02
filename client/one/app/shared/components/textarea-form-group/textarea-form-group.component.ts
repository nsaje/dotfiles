import './textarea-form-group.component.less';

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
import {StatusIconType} from '../../types/status-icon-type';

@Component({
    selector: 'zem-textarea-form-group',
    templateUrl: './textarea-form-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TextAreaFormGroupComponent implements OnInit, OnChanges {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
    @Input()
    value: string;
    @Input()
    statusIcon: StatusIconType;
    @Input()
    placeholder: string;
    @Input()
    maxLength: number;
    @Input()
    rows: number;
    @Input()
    isDisabled: boolean = false;
    @Input()
    isFocused: boolean = false;
    @Input()
    errors: string[];
    @Output()
    valueChange = new EventEmitter<string>();
    @Output()
    inputFocus = new EventEmitter<null>();

    model: string;

    ngOnInit(): void {
        this.rows = commonHelpers.getValueOrDefault(this.rows, 4);
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;
        }
    }

    onBlur($event: string) {
        this.valueChange.emit($event);
    }

    onFocus() {
        this.inputFocus.emit();
    }
}
