import './textarea.component.less';

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
    selector: 'zem-textarea',
    templateUrl: './textarea.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TextAreaComponent implements OnChanges {
    @Input()
    value: string;
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
    hasError: boolean = false;
    @Output()
    valueChange = new EventEmitter<string>();
    @Output()
    inputBlur = new EventEmitter<string>();

    model: string;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;
        }
    }

    onModelChange($event: string) {
        this.valueChange.emit($event);
    }

    onBlur() {
        if (this.model !== this.value) {
            this.inputBlur.emit(this.model);
        }
    }
}
