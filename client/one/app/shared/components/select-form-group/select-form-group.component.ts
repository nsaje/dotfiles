import './select-form-group.component.less';

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
    selector: 'zem-select-form-group',
    templateUrl: './select-form-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SelectFormGroupComponent implements OnChanges {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
    @Input()
    value: string;
    @Input()
    bindLabel: string;
    @Input()
    bindValue: string;
    @Input()
    items: any[];
    @Input()
    placeholder: string;
    @Input()
    isDisabled: boolean = false;
    @Input()
    isSearchable: boolean = false;
    @Input()
    isClearable: boolean = true;
    @Input()
    groupByValue: string;
    @Input()
    orderByValue: string;
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

    onValueChange($event: string) {
        this.valueChange.emit($event);
    }
}
