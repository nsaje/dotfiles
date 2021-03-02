import './text-form-group.component.less';

import {
    Component,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';
import {StatusIconType} from '../../types/status-icon-type';

@Component({
    selector: 'zem-text-form-group',
    templateUrl: './text-form-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TextFormGroupComponent implements OnChanges {
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
    isDisabled: boolean = false;
    @Input()
    isFocused: boolean = false;
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
