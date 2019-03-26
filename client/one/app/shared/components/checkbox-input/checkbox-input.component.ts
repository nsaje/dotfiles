import './checkbox-input.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';

@Component({
    selector: 'zem-checkbox-input',
    templateUrl: './checkbox-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CheckboxInputComponent {
    @Input()
    isChecked: boolean = false;
    @Input()
    isDisabled: boolean = false;
    @Input()
    hasError: boolean = false;
    @Output()
    toggle = new EventEmitter<boolean>();

    onChange() {
        this.toggle.emit(!this.isChecked);
    }
}
