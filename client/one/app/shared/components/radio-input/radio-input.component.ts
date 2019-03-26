import './radio-input.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
    SimpleChanges,
    OnChanges,
} from '@angular/core';

@Component({
    selector: 'zem-radio-input',
    templateUrl: './radio-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RadioInputComponent implements OnChanges {
    @Input()
    groupModel: any;
    @Input()
    value: any;
    @Input()
    isDisabled: boolean = false;
    @Input()
    hasError: boolean = false;
    @Output()
    select = new EventEmitter<any>();

    isChecked: boolean = false;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.groupModel || changes.value) {
            this.isChecked = this.groupModel === this.value;
        }
    }

    onChange() {
        this.select.emit(this.value);
    }
}
