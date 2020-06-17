import './checkbox-input.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
    SimpleChanges,
    OnChanges,
} from '@angular/core';
import {CheckboxInputDisplayState} from './types/checkbox-input-display-state';

@Component({
    selector: 'zem-checkbox-input',
    templateUrl: './checkbox-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CheckboxInputComponent implements OnChanges {
    @Input()
    isChecked: boolean = false;
    @Input()
    isDisabled: boolean = false;
    @Input()
    hasError: boolean = false;
    @Input()
    enableIndeterminateState: boolean = false;
    @Output()
    toggle = new EventEmitter<boolean>();

    displayState: CheckboxInputDisplayState = 'unchecked';

    onChange() {
        this.toggle.emit(this.displayState !== 'checked');
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.isChecked) {
            if (
                this.enableIndeterminateState &&
                this.isChecked !== true &&
                this.isChecked !== false
            ) {
                this.displayState = 'indeterminate';
            } else if (this.isChecked) {
                this.displayState = 'checked';
            } else {
                this.displayState = 'unchecked';
            }
        }
    }
}
