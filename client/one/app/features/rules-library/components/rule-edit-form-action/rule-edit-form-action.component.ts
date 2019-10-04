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
import {RuleAction} from '../../types/rule-action';
import {
    RuleActionType,
    RuleActionFrequency,
    Macro,
} from '../../rules-library.constants';
import {EMAIL_MACROS} from '../../rules-library.config';
import {RuleActionConfig} from '../../types/rule-action-config';
import * as unitsHelpers from '../../../../shared/helpers/units.helpers';

@Component({
    selector: 'zem-rule-edit-form-action',
    templateUrl: './rule-edit-form-action.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormActionComponent implements OnChanges {
    @Input()
    ruleAction: RuleAction;
    @Input()
    availableActions: RuleActionConfig[];
    @Output()
    ruleActionChange = new EventEmitter<RuleAction>();

    selectedActionConfig: RuleActionConfig;
    selectedMacro: Macro;
    shouldAppendMacroToSubject = true;
    availableActionFrequencies: {label: string; value: RuleActionFrequency}[];
    RuleActionType = RuleActionType;
    EMAIL_MACROS = EMAIL_MACROS;

    // TODO (automation-rules): Return correct currency symbol
    getUnitText = unitsHelpers.getUnitText;

    ngOnChanges(changes: SimpleChanges) {
        if (changes.ruleAction) {
            this.selectedActionConfig = this.getSelectedActionConfig();
            this.availableActionFrequencies = this.getAvailableActionFrequencies();
        }
    }

    selectType(type: RuleActionType) {
        const updatedAction: RuleAction = {
            ...this.ruleAction,
            type: type,
        };
        if (!updatedAction.type) {
            updatedAction.frequency = null;
        }
        // TODO (automation-rules): Should we reset email fields too? Maybe reset it on "Save" if ruleAction.type !== "SEND_EMAIL"
        this.ruleActionChange.emit(updatedAction);
    }

    updateValue(value: number) {
        this.ruleActionChange.emit({...this.ruleAction, value: value});
    }

    updateLimit(limit: number) {
        this.ruleActionChange.emit({...this.ruleAction, limit: limit});
    }

    selectFrequency(frequency: RuleActionFrequency) {
        this.ruleActionChange.emit({...this.ruleAction, frequency: frequency});
    }

    updateEmailSubject(emailSubject: string) {
        this.shouldAppendMacroToSubject = true;
        this.ruleActionChange.emit({
            ...this.ruleAction,
            emailSubject: emailSubject,
        });
    }

    updateEmailBody(emailBody: string) {
        this.shouldAppendMacroToSubject = false;
        this.ruleActionChange.emit({
            ...this.ruleAction,
            emailBody: emailBody,
        });
    }

    updateEmailRecipients(emailRecipients: string) {
        this.ruleActionChange.emit({
            ...this.ruleAction,
            emailRecipients: emailRecipients,
        });
    }

    selectMacro(macro: Macro) {
        this.selectedMacro = macro;
    }

    appendSelectedMacro() {
        if (this.shouldAppendMacroToSubject) {
            this.updateEmailSubject(
                `${this.ruleAction.emailSubject || ''}${this.selectedMacro}`
            );
        } else {
            this.updateEmailBody(
                `${this.ruleAction.emailBody || ''}${this.selectedMacro}`
            );
        }
    }

    getSelectedActionConfig() {
        return (
            this.availableActions.find(action => {
                return action.type === this.ruleAction.type;
            }) || {label: null, type: null, frequencies: []}
        );
    }

    getAvailableActionFrequencies(): {
        label: string;
        value: RuleActionFrequency;
    }[] {
        return this.selectedActionConfig.frequencies.map(frequency => {
            return {value: frequency, label: this.getFrequencyLabel(frequency)};
        });
    }

    getFrequencyLabel(frequency: RuleActionFrequency): string {
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
