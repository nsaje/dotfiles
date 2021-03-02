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
import {StatusIconType} from '../../types/status-icon-type';

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
    statusIcon: StatusIconType;
    @Input()
    bindLabel: string;
    @Input()
    bindValue: string;
    @Input()
    appendTo: 'body';
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
    closeOnSelect: boolean = true;
    @Input()
    clearSearchOnSelect: boolean = false;
    @Input()
    isLoading: boolean = false;
    @Input()
    searchFn: Function;
    @Input()
    addCustomItemFn: (term: string) => any | Promise<any>;
    @Input()
    addCustomItemText: string;
    @Input()
    debounceTime: number;
    @Input()
    errors: string[];
    @Input()
    searchOnFocus: boolean = false;
    @Input()
    loadingText: string;
    @Output()
    valueChange = new EventEmitter<string>();
    @Output()
    search = new EventEmitter<string>();
    @Output()
    open = new EventEmitter<void>();

    model: string;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;
        }
    }

    onValueChange($event: string) {
        this.valueChange.emit($event);
    }

    onSearch($event: string) {
        this.search.emit($event);
    }
}
