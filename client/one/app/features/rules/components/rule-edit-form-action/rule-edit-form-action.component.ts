import './rule-edit-form-action.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
    OnInit,
} from '@angular/core';
import {
    RuleActionType,
    RuleActionFrequency,
    Macro,
    RuleTargetType,
} from '../../../../core/rules/rules.constants';
import {RuleActionConfig} from '../../../../core/rules/types/rule-action-config';
import * as unitsHelpers from '../../../../shared/helpers/units.helpers';
import {FieldErrors} from '../../../../shared/types/field-errors';
import {
    EMAIL_MACROS,
    RULE_TARGET_TYPES,
    RULE_ACTIONS_OPTIONS,
} from '../../rules.config';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';

@Component({
    selector: 'zem-rule-edit-form-action',
    templateUrl: './rule-edit-form-action.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormActionComponent implements OnChanges, OnInit {
    @Input()
    actionType: RuleActionType;
    @Input()
    targetType: RuleTargetType;
    @Input()
    actionFrequency: RuleActionFrequency;
    @Input()
    changeStep: number;
    @Input()
    changeLimit: number;
    @Input()
    sendEmailRecipients: string;
    @Input()
    sendEmailSubject: string;
    @Input()
    sendEmailBody: string;
    @Input()
    availableActions: RuleActionConfig[];
    @Input()
    availablePublisherGroups: PublisherGroup[];
    @Input()
    isSearchLoading: boolean;
    @Input()
    actionTypeErrors: FieldErrors;
    @Input()
    actionFrequencyErrors: FieldErrors;
    @Input()
    changeStepErrors: FieldErrors;
    @Input()
    changeLimitErrors: FieldErrors;
    @Input()
    sendEmailRecipientsErrors: FieldErrors;
    @Input()
    sendEmailSubjectErrors: FieldErrors;
    @Input()
    sendEmailBodyErrors: FieldErrors;
    @Input()
    publisherGroupIdErrors: FieldErrors;
    @Output()
    targetActionChange = new EventEmitter<{
        targetType: RuleTargetType;
        actionType: RuleActionType;
    }>();
    @Output()
    actionFrequencyChange = new EventEmitter<number>();
    @Output()
    changeStepChange = new EventEmitter<number>();
    @Output()
    changeLimitChange = new EventEmitter<number>();
    @Output()
    sendEmailRecipientsChange = new EventEmitter<string>();
    @Output()
    sendEmailSubjectChange = new EventEmitter<string>();
    @Output()
    sendEmailBodyChange = new EventEmitter<string>();
    @Output()
    publisherGroupChange = new EventEmitter<string>();
    @Output()
    publisherGroupsSearch = new EventEmitter<string>();
    @Output()
    publisherGroupsOpen = new EventEmitter<void>();

    selectedTargetAndActionType: string;
    selectedActionConfig: RuleActionConfig;
    selectedMacro: Macro;
    shouldAppendMacroToSubject = true;
    publisherGroupId: string;
    availableActionFrequencies: {label: string; value: number}[];
    availablePublisherGroupsItems: {label: string; value: string}[];
    availableTargetAndActionTypes: {
        label: string;
        value: string;
        actionType: RuleActionType;
        targetType: RuleTargetType;
    }[];
    RuleActionType = RuleActionType;
    EMAIL_MACROS = EMAIL_MACROS;

    // TODO (automation-rules): Return correct currency symbol
    getUnitText = unitsHelpers.getUnitText;

    ngOnInit(): void {
        this.availableTargetAndActionTypes = this.constructAvailableTargetAndActionTypes();
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.actionType || changes.targetType) {
            this.selectedTargetAndActionType = this.prepareSelectedTArgetAndActionType(
                this.targetType,
                this.actionType
            );
            this.selectedActionConfig = this.getActionConfig(this.actionType);
            this.availableActionFrequencies = this.getAvailableActionFrequencies(
                this.selectedActionConfig
            );
        }

        if (changes.availablePublisherGroups) {
            this.availablePublisherGroupsItems = this.getAvailablePublisherGroupsItems(
                this.availablePublisherGroups
            );
        }
    }

    selectTargetAndActionType(targetActionType: string) {
        const selectedTargetAndActionType = this.getSelectedTargetAndActionType(
            targetActionType
        );
        this.targetActionChange.emit({
            targetType: selectedTargetAndActionType.targetType,
            actionType: selectedTargetAndActionType.actionType,
        });
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

    updatePublisherGroup(publisherGroupId: string) {
        this.publisherGroupChange.emit(publisherGroupId);
    }

    updateSendEmailSubject(sendEmailSubject: string) {
        this.sendEmailSubjectChange.emit(sendEmailSubject);
    }

    updateSendEmailBody(sendEmailBody: string) {
        this.sendEmailBodyChange.emit(sendEmailBody);
    }

    updateSendEmailRecipients(sendEmailRecipients: string) {
        this.sendEmailRecipientsChange.emit(sendEmailRecipients);
    }

    selectMacro(macro: Macro) {
        this.selectedMacro = macro;
    }

    setShouldAppendMacroToSubject(shouldAppendToSubject: boolean) {
        this.shouldAppendMacroToSubject = shouldAppendToSubject;
    }

    appendSelectedMacro() {
        if (this.shouldAppendMacroToSubject) {
            this.updateSendEmailSubject(
                `${this.sendEmailSubject || ''}{${this.selectedMacro}}`
            );
        } else {
            this.updateSendEmailBody(
                `${this.sendEmailBody || ''}{${this.selectedMacro}}`
            );
        }
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

    private getSelectedTargetAndActionType(
        selectedTargetAndActionType: string
    ) {
        return (
            this.availableTargetAndActionTypes.find(targetAction => {
                return targetAction.value === selectedTargetAndActionType;
            }) || {
                label: '',
                value: '',
                targetType: this.targetType,
                actionType: this.actionType,
            }
        );
    }

    private constructAvailableTargetAndActionTypes(): {
        label: string;
        value: string;
        targetType: RuleTargetType;
        actionType: RuleActionType;
    }[] {
        const availableActions: {
            label: string;
            value: string;
            targetType: RuleTargetType;
            actionType: RuleActionType;
        }[] = [];
        RULE_TARGET_TYPES.forEach(target => {
            target.availableActions.forEach(action => {
                const actionConfig = this.getActionConfig(action);
                availableActions.push({
                    label: target.label + ' - ' + actionConfig.label,
                    value: this.prepareSelectedTArgetAndActionType(
                        target.value,
                        actionConfig.type
                    ),
                    targetType: target.value,
                    actionType: actionConfig.type,
                });
            });
        });
        return availableActions;
    }

    private prepareSelectedTArgetAndActionType(
        targetType: RuleTargetType,
        actionType: RuleActionType
    ): string {
        return targetType + ':' + actionType;
    }

    private getActionConfig(actionType: RuleActionType): RuleActionConfig {
        return (
            RULE_ACTIONS_OPTIONS[actionType] || {
                label: null,
                type: null,
                frequencies: [],
            }
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

    private getAvailablePublisherGroupsItems(
        availablePublisherGroups: PublisherGroup[]
    ): {label: string; value: string}[] {
        return availablePublisherGroups.map(publisherGroup => {
            return {
                value: publisherGroup.id,
                label: publisherGroup.name,
            };
        });
    }
}
