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
    RULE_ACTION_TYPES_OPTIONS,
    RULE_ACTION_FREQUENCY_OPTIONS,
    RULE_CURRENCY_HELP_TEXT,
    RULE_ACTION_DISABLED_HELP_TEXT,
    RULE_PLACEMENT_TARGET_TEXT,
    RULE_PUBLISHER_TARGET_TEXT,
} from '../../rules.config';
import {PublisherGroup} from '../../../../core/publisher-groups/types/publisher-group';
import {Unit} from '../../../../app.constants';

@Component({
    selector: 'zem-rule-edit-form-action',
    templateUrl: './rule-edit-form-action.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormActionComponent implements OnChanges, OnInit {
    @Input()
    ruleId: string;
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
    publisherGroup: PublisherGroup;
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
    publisherGroupErrors: FieldErrors;
    @Input()
    isDisabled: boolean = false;
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
    publisherGroupChange = new EventEmitter<PublisherGroup>();
    @Output()
    publisherGroupsSearch = new EventEmitter<string>();
    @Output()
    publisherGroupsOpen = new EventEmitter<void>();

    selectedTargetAndActionType: string;
    selectedActionConfig: RuleActionConfig;
    selectedMacro: Macro;
    shouldAppendMacroToSubject = true;
    availableActionFrequencies: {label: string; value: number}[];
    availablePublisherGroupsItems: {label: string; value: string}[];
    availableTargetAndActionTypes: {
        label: string;
        value: string;
        actionType: RuleActionType;
        targetType: RuleTargetType;
    }[];
    formattedChangeStep: number;
    formattedChangeLimit: number;
    inputUnitSymbol: string;
    inputHelpText: string;
    actionHoverText: string;
    actionHelpText: string;

    RuleActionType = RuleActionType;

    EMAIL_MACROS = EMAIL_MACROS;

    ngOnInit(): void {
        this.availableTargetAndActionTypes = this.constructAvailableTargetAndActionTypes();
        this.availablePublisherGroupsItems = this.getAvailablePublisherGroupsItems(
            this.availablePublisherGroups
        );
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.actionType || changes.targetType) {
            this.selectedTargetAndActionType = this.prepareSelectedTargetAndActionType(
                this.targetType,
                this.actionType
            );
            this.selectedActionConfig = this.getActionTypeConfig(
                this.actionType
            );
            this.availableActionFrequencies = this.getAvailableActionFrequencies(
                this.selectedActionConfig
            );
        }

        if (changes.availablePublisherGroups || changes.publisherGroup) {
            this.availablePublisherGroupsItems = this.getAvailablePublisherGroupsItems(
                this.availablePublisherGroups
            );
        }

        this.formattedChangeStep = this.formatChangeStep(
            this.changeStep,
            this.actionType
        );
        this.formattedChangeLimit = this.formatChangeLimit(
            this.changeLimit,
            this.actionType
        );
        this.inputUnitSymbol =
            this.selectedActionConfig.unit === Unit.CurrencySign
                ? '¤'
                : unitsHelpers.getUnitText(this.selectedActionConfig.unit);
        this.actionHoverText = this.ruleId
            ? RULE_ACTION_DISABLED_HELP_TEXT
            : null;
        this.inputHelpText =
            this.selectedActionConfig.unit === Unit.CurrencySign
                ? RULE_CURRENCY_HELP_TEXT
                : null;

        if (this.targetType === RuleTargetType.AdGroupPublisher) {
            this.actionHelpText = RULE_PUBLISHER_TARGET_TEXT;
        }

        if (this.targetType === RuleTargetType.AdGroupPlacement) {
            this.actionHelpText = RULE_PLACEMENT_TARGET_TEXT;
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
        const publisherGroup = this.availablePublisherGroups.find(
            pg => pg.id === publisherGroupId
        );
        this.publisherGroupChange.emit(publisherGroup);
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

    private formatChangeStep(changeStep: number, actionType: RuleActionType) {
        if (
            changeStep &&
            (actionType === RuleActionType.IncreaseBidModifier ||
                actionType === RuleActionType.DecreaseBidModifier)
        ) {
            return changeStep * 100.0;
        }
        return changeStep;
    }

    private formatChangeLimit(changeLimit: number, actionType: RuleActionType) {
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
        valueLabel: string;
        group: string;
        targetType: RuleTargetType;
        actionType: RuleActionType;
    }[] {
        const availableActions: {
            label: string;
            value: string;
            valueLabel: string;
            group: string;
            targetType: RuleTargetType;
            actionType: RuleActionType;
        }[] = [];
        RULE_TARGET_TYPES.forEach(target => {
            target.availableActions.forEach(action => {
                const actionTypeConfig = this.getActionTypeConfig(action.type);
                availableActions.push({
                    group: target.label,
                    label: action.label,
                    valueLabel: actionTypeConfig.valueLabel,
                    value: this.prepareSelectedTargetAndActionType(
                        target.value,
                        actionTypeConfig.type
                    ),
                    targetType: target.value,
                    actionType: actionTypeConfig.type,
                });
            });
        });
        return availableActions;
    }

    private prepareSelectedTargetAndActionType(
        targetType: RuleTargetType,
        actionType: RuleActionType
    ): string {
        return targetType + ':' + actionType;
    }

    private getActionTypeConfig(actionType: RuleActionType): RuleActionConfig {
        return (
            RULE_ACTION_TYPES_OPTIONS[actionType] || {
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
            return (
                RULE_ACTION_FREQUENCY_OPTIONS[frequency] || {
                    label: null,
                    value: null,
                }
            );
        });
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
