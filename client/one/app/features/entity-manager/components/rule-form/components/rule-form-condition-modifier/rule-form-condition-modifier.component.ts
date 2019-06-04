import './rule-form-condition-modifier.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    SimpleChanges,
    Output,
    EventEmitter,
} from '@angular/core';
import {RuleConditionOperandModifier} from '../../types/rule-condition-operand-modifier';
import * as clone from 'clone';
import {
    TimeRange,
    ValueModifierType,
    RuleConditionProperty,
} from '../../rule-form.constants';

@Component({
    selector: 'zem-rule-form-condition-modifier',
    templateUrl: './rule-form-condition-modifier.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleFormConditionModifierComponent implements OnChanges {
    @Input()
    value: string;
    @Input()
    property: RuleConditionProperty;
    @Input()
    modifier: RuleConditionOperandModifier;
    @Output()
    modifierChange = new EventEmitter<RuleConditionOperandModifier>();

    model: RuleConditionOperandModifier;
    propertyText: string = '';
    TimeRange = TimeRange;
    availableModifierTypes: any[] = [
        {
            name: 'Increase',
            value: ValueModifierType.IncreaseValue,
        },
        {
            name: 'Decrease',
            value: ValueModifierType.DecreaseValue,
        },
    ];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.modifier) {
            this.model = clone(this.modifier);
            this.propertyText = this.getPropertyText();
        }
    }

    setTimeRange($event: TimeRange) {
        this.model.timeRange = $event;
    }

    save() {
        this.modifierChange.emit(clone(this.model));
    }

    cancel() {
        this.modifierChange.emit(clone(this.modifier));
    }

    onTypeChange($event: ValueModifierType) {
        this.model.valueModifier.type = $event;
    }

    onValueChange($event: number) {
        this.model.valueModifier.value = $event;
    }

    getPropertyText() {
        if (this.property === RuleConditionProperty.TotalSpend) {
            return 'total spend by';
        } else if (this.property === RuleConditionProperty.Impressions) {
            return 'impressions by';
        } else if (this.property === RuleConditionProperty.DailyBudget) {
            return 'daily budget by';
        }
        return `${this.value} by`;
    }
}
