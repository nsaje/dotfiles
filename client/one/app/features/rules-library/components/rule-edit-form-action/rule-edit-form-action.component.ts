import './rule-edit-form-action.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {
    RuleActionType,
    RuleActionFrequency,
} from '../../../../core/rules/rules.constants';
import {RuleActionConfig} from '../../../../core/rules/types/rule-action-config';
import * as unitsHelpers from '../../../../shared/helpers/units.helpers';

@Component({
    selector: 'zem-rule-edit-form-action',
    templateUrl: './rule-edit-form-action.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormActionComponent implements OnChanges {
    @Input()
    actionType: RuleActionType;
    @Input()
    actionFrequency: RuleActionFrequency;
    @Input()
    changeStep: number;
    @Input()
    changeLimit: number;
    @Input()
    availableActions: RuleActionConfig[];
    @Output()
    actionTypeChange = new EventEmitter<RuleActionType>();
    @Output()
    actionFrequencyChange = new EventEmitter<number>();
    @Output()
    changeStepChange = new EventEmitter<number>();
    @Output()
    changeLimitChange = new EventEmitter<number>();

    selectedActionConfig: RuleActionConfig;
    availableActionFrequencies: {label: string; value: number}[];
    RuleActionType = RuleActionType;

    // TODO (automation-rules): Return correct currency symbol
    getUnitText = unitsHelpers.getUnitText;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.actionType) {
            this.selectedActionConfig = this.getSelectedActionConfig(
                this.availableActions,
                this.actionType
            );
            this.availableActionFrequencies = this.getAvailableActionFrequencies(
                this.selectedActionConfig
            );
        }
    }

    selectActionType(actionType: RuleActionType) {
        this.actionTypeChange.emit(actionType);
    }

    selectActionFrequency(actionFrequency: number) {
        this.actionFrequencyChange.emit(actionFrequency);
    }

    updateChangeStep(changeStep: number, actionType: RuleActionType) {
        if (
            actionType === RuleActionType.IncreaseBidModifier ||
            actionType === RuleActionType.DecreaseBidModifier
        ) {
            changeStep = changeStep / 100.0;
        }
        this.changeStepChange.emit(changeStep);
    }

    updateChangeLimit(changeLimit: number, actionType: RuleActionType) {
        if (
            actionType === RuleActionType.IncreaseBidModifier ||
            actionType === RuleActionType.DecreaseBidModifier
        ) {
            changeLimit = changeLimit / 100.0 + 1;
        }
        this.changeLimitChange.emit(changeLimit);
    }

    formatChangeStep(changeStep: number, actionType: RuleActionType) {
        if (
            changeStep &&
            (actionType === RuleActionType.IncreaseBidModifier ||
                actionType === RuleActionType.DecreaseBidModifier)
        ) {
            return changeStep * 100.0;
        }
        return changeStep;
    }

    formatChangeLimit(changeLimit: number, actionType: RuleActionType) {
        if (
            changeLimit &&
            (actionType === RuleActionType.IncreaseBidModifier ||
                actionType === RuleActionType.DecreaseBidModifier)
        ) {
            return (changeLimit - 1) * 100.0;
        }
        return changeLimit;
    }

    private getSelectedActionConfig(
        availableActions: RuleActionConfig[],
        actionType: RuleActionType
    ): RuleActionConfig {
        return (
            availableActions.find(action => {
                return action.type === actionType;
            }) || {label: null, type: null, frequencies: []}
        );
    }

    private getAvailableActionFrequencies(
        selectedActionConfig: RuleActionConfig
    ): {
        label: string;
        value: number;
    }[] {
        return selectedActionConfig.frequencies.map(frequency => {
            return {
                value: this.getFrequencyValue(frequency),
                label: this.getFrequencyLabel(frequency),
            };
        });
    }

    private getFrequencyValue(frequency: RuleActionFrequency): number {
        switch (frequency) {
            case RuleActionFrequency.Day1:
                return 24;
            case RuleActionFrequency.Days3:
                return 72;
            case RuleActionFrequency.Days7:
                return 168;
        }
    }

    private getFrequencyLabel(frequency: RuleActionFrequency): string {
        switch (frequency) {
            case RuleActionFrequency.Day1:
                return '1 day';
            case RuleActionFrequency.Days3:
                return '3 days';
            case RuleActionFrequency.Days7:
                return '7 days';
        }
    }
}
