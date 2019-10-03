import './integer-form-group.component.less';

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
    selector: 'zem-integer-form-group',
    templateUrl: './integer-form-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class IntegerFormGroupComponent implements OnChanges {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
    @Input()
    value: string;
    @Input()
    placeholder: string;
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
