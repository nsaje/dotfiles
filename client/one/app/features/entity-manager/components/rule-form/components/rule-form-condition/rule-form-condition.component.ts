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
import {RULE_CONDITION_PROPERTIES} from '../../rule-form.config';

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

    firstOperandProperties: any[] = RULE_CONDITION_PROPERTIES;
    operators: any[] = [];
    secondOperandProperties: any[] = [];

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
        this.model.operator = null;
        this.model.secondOperand = {
            property: null,
            value: null,
            modifier: {
                timeRangeModifier: null,
                valueModifier: null,
            },
        };

        this.operators = [];
        this.secondOperandProperties = [];

        if (this.model.firstOperand.property) {
            const propertyConfig = this.firstOperandProperties.find(
                (property: any) => {
                    return property.value === $event;
                }
            );

            if (propertyConfig.hasTimeRangeModifier) {
                this.model.firstOperand.modifier.timeRangeModifier =
                    this.model.firstOperand.modifier.timeRangeModifier || {};
            } else {
                this.model.firstOperand.modifier.timeRangeModifier = null;
            }
            if (propertyConfig.hasValueModifier) {
                this.model.firstOperand.modifier.valueModifier =
                    this.model.firstOperand.modifier.valueModifier || {};
            } else {
                this.model.firstOperand.modifier.valueModifier = null;
            }

            this.operators = propertyConfig.operators;

            propertyConfig.rightOperandProperties.forEach(
                (property: RuleConditionProperty) => {
                    if (property === RuleConditionProperty.FixedValue) {
                        this.secondOperandProperties.push({
                            name: 'Fixed value',
                            value: RuleConditionProperty.FixedValue,
                            hasTimeRangeModifier: false,
                            hasValueModifier: false,
                        });
                    } else {
                        this.secondOperandProperties.push(
                            this.firstOperandProperties.find(item => {
                                return item.value === property;
                            })
                        );
                    }
                }
            );
        }
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
        if (!this.model.operator) {
            this.model.secondOperand = {
                property: null,
                value: null,
                modifier: {
                    timeRangeModifier: null,
                    valueModifier: null,
                },
            };
        }
        this.conditionChange.emit(clone(this.model));
    }

    onSecondOperandPropertyChange($event: RuleConditionProperty) {
        this.model.secondOperand.property = $event;

        const propertyConfig = this.secondOperandProperties.find(
            (property: any) => {
                return property.value === $event;
            }
        );

        if (propertyConfig.hasTimeRangeModifier) {
            this.model.secondOperand.modifier.timeRangeModifier =
                this.model.secondOperand.modifier.timeRangeModifier || {};
        } else {
            this.model.secondOperand.modifier.timeRangeModifier = null;
        }
        if (propertyConfig.hasValueModifier) {
            this.model.secondOperand.modifier.valueModifier =
                this.model.secondOperand.modifier.valueModifier || {};
        } else {
            this.model.secondOperand.modifier.valueModifier = null;
        }

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
