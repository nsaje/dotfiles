import './rule-form-condition.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
    ViewChild,
} from '@angular/core';
import {RuleCondition} from '../../types/rule-condition';
import * as clone from 'clone';
import {
    RuleConditionOperator,
    RuleConditionProperty,
    TimeRange,
} from '../../rule-form.constants';
import {RuleConditionOperandModifier} from '../../types/rule-condition-operand-modifier';
import {PopoverDirective} from '../../../../../../shared/components/popover/popover.directive';

@Component({
    selector: 'zem-rule-form-condition',
    templateUrl: './rule-form-condition.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleFormConditionComponent implements OnChanges {
    @Input()
    condition: RuleCondition;
    @Output()
    conditionChange = new EventEmitter<RuleCondition>();
    @Output()
    conditionRemove = new EventEmitter<void>();

    @ViewChild('firstOperandModifierPopover', {read: PopoverDirective})
    firstOperandModifierPopover: PopoverDirective;

    @ViewChild('secondOperandModifierPopover', {read: PopoverDirective})
    secondOperandModifierPopover: PopoverDirective;

    model: RuleCondition;

    RuleConditionProperty = RuleConditionProperty;
    TimeRange = TimeRange;
    availableConditionProperties: any[] = [
        {
            name: 'Total spend',
            value: RuleConditionProperty.TotalSpend,
        },
        {
            name: 'Impressions',
            value: RuleConditionProperty.Impressions,
        },
        {
            name: 'Daily budget',
            value: RuleConditionProperty.DailyBudget,
        },
        {
            name: '$',
            value: RuleConditionProperty.AbsoluteValue,
        },
    ];
    availableConditionOperators: any[] = [
        {
            name: 'is less than',
            value: RuleConditionOperator.LessThan,
        },
        {
            name: 'is greater Than',
            value: RuleConditionOperator.GreaterThan,
        },
        {
            name: 'contains',
            value: RuleConditionOperator.Contains,
        },
        {
            name: 'not contains',
            value: RuleConditionOperator.NotContains,
        },
    ];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.condition) {
            this.model = clone(this.condition);
        }
    }

    removeCondition() {
        this.conditionRemove.emit();
    }

    onFirstOperandPropertyChange($event: RuleConditionProperty) {
        this.model.firstOperand.property = $event;
        this.conditionChange.emit(clone(this.model));
    }

    onFirstOperandValueChange($event: string) {
        this.model.firstOperand.value = $event;
        this.conditionChange.emit(clone(this.model));
    }

    onFirstOperandModifierChange($event: RuleConditionOperandModifier) {
        this.firstOperandModifierPopover.close();
        this.model.firstOperand.modifier = $event;
        this.conditionChange.emit(clone(this.model));
    }

    onOperatorChange($event: RuleConditionOperator) {
        this.model.operator = $event;
        this.conditionChange.emit(clone(this.model));
    }

    onSecondOperandPropertyChange($event: RuleConditionProperty) {
        this.model.secondOperand.property = $event;
        this.conditionChange.emit(clone(this.model));
    }

    onSecondOperandValueChange($event: string) {
        this.model.secondOperand.value = $event;
        this.conditionChange.emit(clone(this.model));
    }

    onSecondOperandModifierChange($event: RuleConditionOperandModifier) {
        this.secondOperandModifierPopover.close();
        this.model.secondOperand.modifier = $event;
        this.conditionChange.emit(clone(this.model));
    }
}
