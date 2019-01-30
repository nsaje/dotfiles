import '@ng-select/ng-select/themes/default.theme.css';
import './select-input.component.less';

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

@Component({
    selector: 'zem-select-input',
    templateUrl: './select-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SelectInputComponent implements OnInit, OnChanges {
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
    isDisabled: boolean;
    @Input()
    hasError: boolean;
    @Output()
    valueChange = new EventEmitter<string>();

    model: string;

    ngOnInit(): void {
        this.bindLabel = commonHelpers.getValueOrDefault(this.bindLabel, '');
        this.bindValue = commonHelpers.getValueOrDefault(this.bindValue, '');
        this.items = commonHelpers.getValueOrDefault(this.items, []);
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;
        }
    }

    onChange($event: any) {
        this.valueChange.emit($event ? $event.value : null);
    }
}
