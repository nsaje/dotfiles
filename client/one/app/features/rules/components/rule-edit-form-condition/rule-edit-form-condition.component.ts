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
import {RuleCondition} from '../../../../core/rules/types/rule-condition';
import {RuleConditionMetric} from '../../../../core/rules/types/rule-condition-metric';
import {
    RuleConditionOperator,
    TimeRange,
    RuleConditionOperandType,
    RuleConditionOperandGroup,
} from '../../../../core/rules/rules.constants';
import {DataType, Unit, ConversionWindow} from '../../../../app.constants';
import {RuleConditionConfig} from '../../../../core/rules/types/rule-condition-config';
import {RuleConditionOperandConfig} from '../../../../core/rules/types/rule-condition-operand-config';
import * as unitsHelpers from '../../../../shared/helpers/units.helpers';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {RuleConditionError} from '../rule-edit-form/types/rule-condition-error';
import {
    RULE_CONDITIONS_OPTIONS,
    RULE_CURRENCY_HELP_TEXT,
} from '../../rules.config';
import {ConversionPixel} from '../../../../core/conversion-pixels/types/conversion-pixel';
import {ConversionPixelAttribution} from '../../../../core/conversion-pixels/conversion-pixel.constants';

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
    @Input()
    availableConversionPixels: ConversionPixel[];
    @Input()
    conditionErrors: RuleConditionError;
    @Input()
    isDisabled: boolean = false;
    @Output()
    conditionChange = new EventEmitter<ChangeEvent<RuleCondition>>();
    @Output()
    conditionRemove = new EventEmitter<RuleCondition>();
    @Output()
    conversionPixelsSearch = new EventEmitter<string | null>();

    availableMetrics: {
        label: string;
        type: RuleConditionOperandType;
        group?: RuleConditionOperandGroup;
    }[];
    availableOperators: {label: string; operator: RuleConditionOperator}[];
    availableValueTypes: {
        label: string;
        type: RuleConditionOperandType;
        group?: RuleConditionOperandGroup;
    }[];
    selectedConditionConfig: RuleConditionConfig;
    selectedMetricConfig: RuleConditionOperandConfig;
    selectedValueConfig: RuleConditionOperandConfig;
    inputUnitSymbol: string;

    isOnlyAbsoluteValue: boolean;
    showPixelSelector: boolean;

    RuleConditionOperandType = RuleConditionOperandType;
    Unit = Unit;
    DataType = DataType;

    RULE_CURRENCY_HELP_TEXT = RULE_CURRENCY_HELP_TEXT;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.availableConditions) {
            this.availableMetrics = this.getAvailableFirstOperands(
                this.availableConditions,
                this.ruleCondition
            );
        }

        if (changes.ruleCondition) {
            this.selectedConditionConfig = this.getSelectedConditionConfig(
                this.availableConditions,
                this.ruleCondition.metric
            );
            this.isOnlyAbsoluteValue = this.getIsOnlyAbsoluteValue(
                this.selectedConditionConfig
            );
            this.availableOperators = this.getAvailableOperators(
                this.selectedConditionConfig
            );
            this.selectedMetricConfig = this.getSelectedFirstOperandConfig(
                this.selectedConditionConfig
            );
            this.selectedValueConfig = this.getSelectedValueConfig(
                this.selectedConditionConfig,
                this.ruleCondition
            );
            this.availableMetrics = this.getAvailableFirstOperands(
                this.availableConditions,
                this.ruleCondition
            );
            this.availableValueTypes = this.getAvailableValueTypes(
                this.selectedConditionConfig,
                this.ruleCondition
            );
            this.showPixelSelector =
                this.ruleCondition.metric.type ===
                    RuleConditionOperandType.Conversions ||
                this.ruleCondition.metric.type ===
                    RuleConditionOperandType.AvgCostPerConversion ||
                this.ruleCondition.metric.type ===
                    RuleConditionOperandType.Roas;

            this.inputUnitSymbol =
                this.selectedValueConfig?.unit === Unit.CurrencySign
                    ? '¤'
                    : unitsHelpers.getUnitText(this.selectedValueConfig?.unit);
        }
    }

    selectMetricType(metricType: RuleConditionOperandType) {
        const isOnlyAbsoluteValueMetric = this.getIsOnlyAbsoluteValue(
            RULE_CONDITIONS_OPTIONS[metricType]
        );

        this.conditionChange.emit({
            target: this.ruleCondition,
            changes: {
                operator: null,
                metric: {
                    type: metricType,
                    modifier: null,
                    window: null,
                    conversionPixel: null,
                    conversionPixelWindow: null,
                    conversionPixelAttribution: null,
                },
                value: {
                    type: isOnlyAbsoluteValueMetric
                        ? RuleConditionOperandType.AbsoluteValue
                        : null,
                    value: null,
                    window: null,
                },
            },
        });
    }

    updateMetricModifier(modifier: string) {
        this.conditionChange.emit({
            target: this.ruleCondition,
            changes: {
                metric: {
                    ...this.ruleCondition.metric,
                    modifier: modifier,
                },
            },
        });
    }

    updateMetricWindow(window: TimeRange) {
        this.conditionChange.emit({
            target: this.ruleCondition,
            changes: {
                metric: {
                    ...this.ruleCondition.metric,
                    window: window,
                },
            },
        });
    }

    updateConversionPixel(conversionPixel: string) {
        this.conditionChange.emit({
            target: this.ruleCondition,
            changes: {
                metric: {
                    ...this.ruleCondition.metric,
                    conversionPixel: conversionPixel,
                },
            },
        });
    }

    updateConversionPixelWindow(conversionWindow: ConversionWindow) {
        this.conditionChange.emit({
            target: this.ruleCondition,
            changes: {
                metric: {
                    ...this.ruleCondition.metric,
                    conversionPixelWindow: conversionWindow,
                },
            },
        });
    }

    updateConversionPixelAttribution(
        conversionAttribution: ConversionPixelAttribution
    ) {
        this.conditionChange.emit({
            target: this.ruleCondition,
            changes: {
                metric: {
                    ...this.ruleCondition.metric,
                    conversionPixelAttribution: conversionAttribution,
                    conversionPixelWindow: null,
                },
            },
        });
    }

    selectOperator(operator: RuleConditionOperator) {
        this.conditionChange.emit({
            target: this.ruleCondition,
            changes: {
                operator: operator,
            },
        });
    }

    selectValueType(operand: RuleConditionOperandType) {
        this.conditionChange.emit({
            target: this.ruleCondition,
            changes: {
                value: {
                    ...this.ruleCondition.value,
                    type: operand,
                    value: null,
                    window: null,
                },
            },
        });
    }

    updateValueValue(value: string) {
        this.conditionChange.emit({
            target: this.ruleCondition,
            changes: {
                value: {
                    ...this.ruleCondition.value,
                    value: value,
                },
            },
        });
    }

    updateValueWindow(window: TimeRange) {
        this.conditionChange.emit({
            target: this.ruleCondition,
            changes: {
                value: {
                    ...this.ruleCondition.value,
                    window: window,
                },
            },
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

    private getSelectedConditionConfig(
        availableConditions: RuleConditionConfig[],
        metric: RuleConditionMetric
    ): RuleConditionConfig {
        if (!metric) {
            return null;
        }
        return (
            availableConditions.find(availableCondition => {
                return availableCondition.metric.type === metric.type;
            }) || null
        );
    }

    private getSelectedFirstOperandConfig(
        selectedConditionConfig: RuleConditionConfig
    ): RuleConditionOperandConfig {
        if (!selectedConditionConfig) {
            return null;
        }
        return selectedConditionConfig.metric;
    }

    private getSelectedValueConfig(
        selectedConditionConfig: RuleConditionConfig,
        ruleCondition: RuleCondition
    ): RuleConditionOperandConfig {
        if (!selectedConditionConfig) {
            return null;
        }

        return (
            selectedConditionConfig.availableValueTypes.find(
                availableOperand => {
                    return availableOperand.type === ruleCondition.value.type;
                }
            ) || null
        );
    }

    private getAvailableFirstOperands(
        availableConditions: RuleConditionConfig[],
        ruleCondition: RuleCondition
    ): {
        label: string;
        type: RuleConditionOperandType;
        group?: RuleConditionOperandGroup;
    }[] {
        return (availableConditions || []).map(availableCondition => {
            return {
                label: this.getOperandLabel(
                    availableCondition.metric,
                    ruleCondition.metric.type,
                    ruleCondition.metric.modifier
                ),
                type: availableCondition.metric.type,
                group: availableCondition.metric.group || null,
            };
        });
    }

    private getAvailableOperators(
        selectedConditionConfig: RuleConditionConfig
    ): {
        label: string;
        operator: RuleConditionOperator;
    }[] {
        if (!selectedConditionConfig) {
            return [];
        }
        return (selectedConditionConfig.availableOperators || []).map(
            operator => {
                return {
                    label: this.getOperatorLabel(operator),
                    operator: operator,
                };
            }
        );
    }

    private getAvailableValueTypes(
        selectedConditionConfig: RuleConditionConfig,
        ruleCondition: RuleCondition
    ): {
        label: string;
        type: RuleConditionOperandType;
        group?: RuleConditionOperandGroup;
    }[] {
        if (!selectedConditionConfig) {
            return [];
        }
        return (selectedConditionConfig.availableValueTypes || []).map(
            operand => {
                return {
                    label: this.getOperandLabel(
                        operand,
                        ruleCondition.value.type,
                        ruleCondition.value.value
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
            case RuleConditionOperator.StartsWith:
                return 'starts with';
            case RuleConditionOperator.EndsWith:
                return 'ends with';
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

    private getIsOnlyAbsoluteValue(
        selectedConditionConfig: RuleConditionConfig
    ): boolean {
        if (!selectedConditionConfig) {
            return true;
        }

        return (
            selectedConditionConfig.availableValueTypes.length === 1 &&
            selectedConditionConfig.availableValueTypes[0].type ===
                RuleConditionOperandType.AbsoluteValue
        );
    }
}
