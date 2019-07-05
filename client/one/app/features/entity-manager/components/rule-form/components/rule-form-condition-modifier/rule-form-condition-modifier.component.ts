import './rule-form-condition-modifier.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    SimpleChanges,
    OnChanges,
} from '@angular/core';
import {TimeRange, Unit, DataType} from '../../rule-form.constants';
import {TIME_RANGES} from '../../rule-form.config';
import {RuleConditionOperandValueModifier} from '../../types/rule-condition-operand-value-modifier';

@Component({
    selector: 'zem-rule-form-condition-modifier',
    templateUrl: './rule-form-condition-modifier.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleFormConditionModifierComponent implements OnChanges {
    @Input()
    value: string;
    @Input()
    valueLabel: string;
    @Input()
    timeRange: TimeRange;
    @Input()
    hasTimeRangeModifier: boolean;
    @Input()
    valueModifier: RuleConditionOperandValueModifier;
    @Output()
    valueChange = new EventEmitter<string>();
    @Output()
    timeRangeChange = new EventEmitter<TimeRange>();

    Unit = Unit;
    DataType = DataType;
    availableTimeRanges = TIME_RANGES;
    availableValueSigns = [
        {label: 'plus', value: ''},
        {label: 'minus', value: '-'},
    ];

    valueSign = '';

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.valueSign = '';
            if (
                this.valueModifier &&
                this.valueModifier.unit === Unit.Day &&
                this.value &&
                this.value.startsWith('-')
            ) {
                this.value = this.value.substring(1);
                this.valueSign = '-';
            }
        }
    }

    updateValue(value: string, sign = '') {
        this.valueChange.emit(`${sign || ''}${value || ''}`);
    }
}
