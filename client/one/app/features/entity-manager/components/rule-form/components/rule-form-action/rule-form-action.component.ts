import './rule-form-action.component.less';

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
import * as clone from 'clone';
import {
    RuleActionType,
    RuleActionFrequency,
    Unit,
    RuleActionMacro,
} from '../../rule-form.constants';
import {RULE_ACTIONS} from '../../rule-form.config';

@Component({
    selector: 'zem-rule-form-action',
    templateUrl: './rule-form-action.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleFormActionComponent implements OnChanges {
    @Input()
    value: RuleAction;
    @Output()
    valueChange = new EventEmitter<RuleAction>();

    model: RuleAction = {};
    ruleActionConfig: any = {};
    RuleActionType = RuleActionType;

    macro: RuleActionMacro = null;
    addMacroToSubject: boolean = true;
    availableActionTypes: any[] = [
        {
            name: RULE_ACTIONS[RuleActionType.IncreaseBudget].name,
            value: RULE_ACTIONS[RuleActionType.IncreaseBudget].type,
        },
        {
            name: RULE_ACTIONS[RuleActionType.DecreaseBudget].name,
            value: RULE_ACTIONS[RuleActionType.DecreaseBudget].type,
        },
        {
            name: RULE_ACTIONS[RuleActionType.SendEmail].name,
            value: RULE_ACTIONS[RuleActionType.SendEmail].type,
        },
    ];
    availableMacros: any[] = [
        {
            name: 'Account name',
            value: RuleActionMacro.AccountName,
        },
        {
            name: 'Campaign name',
            value: RuleActionMacro.CampaignName,
        },
        {
            name: 'Ad group name',
            value: RuleActionMacro.AdGroupName,
        },
        {
            name: 'Ad group daily cap',
            value: RuleActionMacro.AdGroupDailyCap,
        },
        {
            name: 'Total spend (last 1 day)',
            value: RuleActionMacro.TotalSpendLastDay,
        },
        {
            name: 'Total spend (last 3 day)',
            value: RuleActionMacro.TotalSpendLastThreeDays,
        },
        {
            name: 'Total spend (last 7 day)',
            value: RuleActionMacro.TotalSpendLastSevenDays,
        },
        {
            name: 'Total spend (lifetime)',
            value: RuleActionMacro.TotalSpendLifetime,
        },
    ];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.value) {
            this.model = clone(this.value);
            this.ruleActionConfig = this.getRuleActionConfig(this.model.type);
        }
    }

    setType(type: RuleActionType) {
        this.model.type = type;
        if (!this.model.type) {
            this.model.frequency = null;
        }
        this.valueChange.emit(clone(this.model));
    }

    setValue(value: number) {
        this.model.value = value;
        this.valueChange.emit(clone(this.model));
    }

    setUnit(unit: Unit) {
        this.model.unit = unit;
        this.valueChange.emit(clone(this.model));
    }

    setLimit(limit: number) {
        this.model.limit = limit;
        this.valueChange.emit(clone(this.model));
    }

    setFrequency(frequency: RuleActionFrequency) {
        this.model.frequency = frequency;
        this.valueChange.emit(clone(this.model));
    }

    setEmailSubject(emailSubject: string) {
        this.addMacroToSubject = true;
        this.model.emailSubject = emailSubject;
        this.valueChange.emit(clone(this.model));
    }

    setEmailBody(emailBody: string) {
        this.addMacroToSubject = false;
        this.model.emailBody = emailBody;
        this.valueChange.emit(clone(this.model));
    }

    setEmailRecipients(emailRecipients: string) {
        this.model.emailRecipients = emailRecipients;
        this.valueChange.emit(clone(this.model));
    }

    setMacro($event: RuleActionMacro) {
        this.macro = $event;
    }

    addMacro() {
        if (this.addMacroToSubject) {
            this.model.emailSubject = `${this.model.emailSubject || ''} {${
                this.macro
            }}`;
        } else {
            this.model.emailBody = `${this.model.emailBody || ''} {${
                this.macro
            }}`;
        }
        this.valueChange.emit(clone(this.model));
    }

    private getRuleActionConfig(type: RuleActionType) {
        if (!type) {
            return null;
        }
        return RULE_ACTIONS[type];
    }
}
