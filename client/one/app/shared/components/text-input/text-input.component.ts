import './text-input.component.less';

import {
    Component,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    EventEmitter,
    Output,
    Input,
    ContentChild,
    TemplateRef,
} from '@angular/core';
import {StatusIconType} from '../../types/status-icon-type';

@Component({
    selector: 'zem-text-input',
    templateUrl: './text-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TextInputComponent implements OnChanges {
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
    hasError: boolean = false;
    @Output()
    valueChange = new EventEmitter<string>();
    @Output()
    inputBlur = new EventEmitter<string>();

    @ContentChild('loaderTemplate', {read: TemplateRef, static: false})
    loaderTemplate: TemplateRef<any>;

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
