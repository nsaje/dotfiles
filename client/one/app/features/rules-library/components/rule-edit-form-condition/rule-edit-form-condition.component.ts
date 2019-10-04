import './rule-edit-form-condition.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {RuleCondition} from '../../types/rule-condition';
import {
    RuleConditionOperator,
    TimeRange,
    RuleConditionOperandType,
    RuleConditionOperandGroup,
} from '../../rules-library.constants';
import {DataType, Unit} from '../../../../app.constants';
import {RuleConditionConfig} from '../../types/rule-condition-config';
import {RuleConditionOperandConfig} from '../../types/rule-condition-operand-config';
import * as unitsHelpers from '../../../../shared/helpers/units.helpers';

@Component({
    selector: 'zem-rule-edit-form-condition',
    templateUrl: './rule-edit-form-condition.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormConditionComponent implements OnChanges {
    @Input()
    ruleCondition: RuleCondition;
    @Input()
    availableConditions: RuleConditionConfig[];
    @Output()
    conditionChange = new EventEmitter<RuleCondition>();
    @Output()
    conditionRemove = new EventEmitter<RuleCondition>();

    availableFirstOperands: {
        label: string;
        type: RuleConditionOperandType;
        group?: RuleConditionOperandGroup;
    }[];
    availableOperators: {label: string; operator: RuleConditionOperator}[];
    availableSecondOperands: {
        label: string;
        type: RuleConditionOperandType;
        group?: RuleConditionOperandGroup;
    }[];
    selectedConditionConfig: RuleConditionConfig;
    selectedFirstOperandConfig: RuleConditionOperandConfig;
    selectedSecondOperandConfig: RuleConditionOperandConfig;

    RuleConditionOperandType = RuleConditionOperandType;
    Unit = Unit;
    DataType = DataType;

    // TODO (automation-rules): Return correct currency symbol
    getUnitText = unitsHelpers.getUnitText;

    // TODO (automation-rules): When unit === Date, operand value must be converted from/to string
    ngOnChanges(changes: SimpleChanges): void {
        if (changes.availableConditions) {
            this.availableFirstOperands = this.getAvailableFirstOperands();
            this.availableOperators = [];
            this.availableSecondOperands = [];
        }

        if (changes.ruleCondition) {
            this.selectedConditionConfig = this.getSelectedConditionConfig();
            this.availableOperators = this.getAvailableOperators();
            this.selectedFirstOperandConfig = this.getSelectedFirstOperandConfig();
            this.selectedSecondOperandConfig = this.getSelectedSecondOperandConfig();
            this.availableFirstOperands = this.getAvailableFirstOperands();
            this.availableSecondOperands = this.getAvailableSecondOperands();
        }
    }

    selectFirstOperand(operand: RuleConditionOperandType) {
        this.conditionChange.emit({
            ...this.ruleCondition,
            firstOperand: operand,
            firstOperandValue: null,
            firstOperandTimeRange: TimeRange.Lifetime,
            operator: null,
            secondOperand: null,
            secondOperandValue: null,
            secondOperandTimeRange: TimeRange.Lifetime,
        });
    }

    updateFirstOperandValue(value: string) {
        this.conditionChange.emit({
            ...this.ruleCondition,
            firstOperandValue: value,
        });
    }

    updateFirstOperandTimeRange(timeRange: TimeRange) {
        this.conditionChange.emit({
            ...this.ruleCondition,
            firstOperandTimeRange: timeRange,
        });
    }

    selectOperator(operator: RuleConditionOperator) {
        this.conditionChange.emit({
            ...this.ruleCondition,
            operator: operator,
        });
    }

    selectSecondOperand(operand: RuleConditionOperandType) {
        this.conditionChange.emit({
            ...this.ruleCondition,
            secondOperand: operand,
            secondOperandValue: null,
            secondOperandTimeRange: TimeRange.Lifetime,
        });
    }

    updateSecondOperandValue(value: string) {
        this.conditionChange.emit({
            ...this.ruleCondition,
            secondOperandValue: value,
        });
    }

    updateSecondOperandTimeRange(timeRange: TimeRange) {
        this.conditionChange.emit({
            ...this.ruleCondition,
            secondOperandTimeRange: timeRange,
        });
    }

    removeCondition() {
        this.conditionRemove.emit(this.ruleCondition);
    }

    areModifiersAvailable(operandConfig: RuleConditionOperandConfig): boolean {
        if (!operandConfig) {
            return false;
        }
        return (
            operandConfig.hasTimeRangeModifier || !!operandConfig.valueModifier
        );
    }

    private getSelectedConditionConfig(): RuleConditionConfig {
        if (!this.ruleCondition.firstOperand) {
            return null;
        }
        return (
            this.availableConditions.find(availableCondition => {
                return (
                    availableCondition.firstOperand.type ===
                    this.ruleCondition.firstOperand
                );
            }) || null
        );
    }

    private getSelectedFirstOperandConfig(): RuleConditionOperandConfig {
        if (!this.selectedConditionConfig) {
            return null;
        }
        return this.selectedConditionConfig.firstOperand;
    }

    private getSelectedSecondOperandConfig(): RuleConditionOperandConfig {
        if (!this.selectedConditionConfig) {
            return null;
        }
        return (
            this.selectedConditionConfig.availableSecondOperands.find(
                availableOperand => {
                    return (
                        availableOperand.type ===
                        this.ruleCondition.secondOperand
                    );
                }
            ) || null
        );
    }

    private getAvailableFirstOperands(): {
        label: string;
        type: RuleConditionOperandType;
        group?: RuleConditionOperandGroup;
    }[] {
        return (this.availableConditions || []).map(availableCondition => {
            return {
                label: this.getOperandLabel(
                    availableCondition.firstOperand,
                    this.ruleCondition.firstOperand,
                    this.ruleCondition.firstOperandValue
                ),
                type: availableCondition.firstOperand.type,
                group: availableCondition.firstOperand.group || null,
            };
        });
    }

    private getAvailableOperators(): {
        label: string;
        operator: RuleConditionOperator;
    }[] {
        if (!this.selectedConditionConfig) {
            return [];
        }
        return (this.selectedConditionConfig.availableOperators || []).map(
            operator => {
                return {
                    label: this.getOperatorLabel(operator),
                    operator: operator,
                };
            }
        );
    }

    private getAvailableSecondOperands(): {
        label: string;
        type: RuleConditionOperandType;
        group?: RuleConditionOperandGroup;
    }[] {
        if (!this.selectedConditionConfig) {
            return [];
        }
        return (this.selectedConditionConfig.availableSecondOperands || []).map(
            operand => {
                return {
                    label: this.getOperandLabel(
                        operand,
                        this.ruleCondition.secondOperand,
                        this.ruleCondition.secondOperandValue
                    ),
                    type: operand.type,
                    group: operand.group || null,
                };
            }
        );
    }

    private getOperatorLabel(operator: RuleConditionOperator): string {
        switch (operator) {
            case RuleConditionOperator.Equals:
                return 'is equal to';
            case RuleConditionOperator.NotEquals:
                return 'is not equal to';
            case RuleConditionOperator.LessThan:
                return 'is less than';
            case RuleConditionOperator.GreaterThan:
                return 'is greater than';
            case RuleConditionOperator.Contains:
                return 'contains';
            case RuleConditionOperator.NotContains:
                return "doesn't contain";
        }
    }

    private getOperandLabel(
        operand: RuleConditionOperandConfig,
        selectedOperand: RuleConditionOperandType,
        selectedOperandValue: string
    ): string {
        if (
            !operand.valueModifier ||
            !selectedOperandValue ||
            operand.type !== selectedOperand
        ) {
            return operand.label;
        }
        return this.getOperandLabelWithValueModifier(
            operand.label,
            selectedOperandValue,
            operand.valueModifier.unit
        );
    }

    private getOperandLabelWithValueModifier(
        label: string,
        value: string,
        unit: Unit
    ): string {
        switch (unit) {
            case Unit.Percent:
                return `${value}% of ${label}`;
            case Unit.Day:
                return this.getLabelForModifiedDateValue(value, label);
            default:
                return label;
        }
    }

    private getLabelForModifiedDateValue(value: string, label: string): string {
        if (['-', '0', '-0'].indexOf(value) !== -1) {
            return label;
        }
        let valueSignText = 'plus';
        if (value && value.startsWith('-')) {
            value = value.substring(1);
            valueSignText = 'minus';
        }
        return `${label} ${valueSignText} ${value} day(s)`;
    }
}
