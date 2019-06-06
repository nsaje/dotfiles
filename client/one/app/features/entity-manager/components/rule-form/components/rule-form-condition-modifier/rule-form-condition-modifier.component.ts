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
import {RULE_CONDITION_PROPERTIES} from '../../rule-form.config';

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
        this.model.timeRangeModifier.value = $event;
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

    private getPropertyText() {
        if (this.property === RuleConditionProperty.FixedValue) {
            return `${this.value} by`;
        } else {
            const propertyConfig = RULE_CONDITION_PROPERTIES.find(
                (property: any) => {
                    return property.value === this.property;
                }
            );
            return `${propertyConfig.name} by`;
        }
    }
}
