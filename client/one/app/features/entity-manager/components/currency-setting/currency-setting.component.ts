import './currency-setting.component.less';

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
    selector: 'zem-currency-setting',
    templateUrl: './currency-setting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CurrencySettingComponent implements OnChanges {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
    @Input()
    infoMessage: string;
    @Input()
    value: string;
    @Input()
    placeholder: string;
    @Input()
    isDisabled: boolean;
    @Input()
    currencySymbol: string;
    @Input()
    fractionSize: number;
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