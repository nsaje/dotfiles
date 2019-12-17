import './rule-edit-form-condition-modifier.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    SimpleChanges,
    OnChanges,
} from '@angular/core';
import {TimeRange} from '../../../../core/rules/rules.constants';
import {DataType, Unit} from '../../../../app.constants';
import {TIME_RANGES} from '../../rules-library.config';
import {RuleConditionOperandValueModifier} from '../../../../core/rules/types/rule-condition-operand-value-modifier';

@Component({
    selector: 'zem-rule-edit-form-condition-modifier',
    templateUrl: './rule-edit-form-condition-modifier.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormConditionModifierComponent implements OnChanges {
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
