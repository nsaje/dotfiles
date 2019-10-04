import './rule-edit-form-conditions.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {RuleCondition} from '../../types/rule-condition';
import * as ruleFormHelpers from '../rule-edit-form/helpers/rule-edit-form.helpers';
import {RuleConditionConfig} from '../../types/rule-condition-config';
import {TimeRange} from '../../rules-library.constants';

@Component({
    selector: 'zem-rule-edit-form-conditions',
    templateUrl: './rule-edit-form-conditions.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormConditionsComponent {
    @Input()
    ruleConditions: RuleCondition[];
    @Input()
    availableConditions: RuleConditionConfig[];
    @Output()
    ruleConditionsChange = new EventEmitter<RuleCondition[]>();

    addCondition() {
        this.ruleConditionsChange.emit([
            ...this.ruleConditions,
            this.generateNewCondition(),
        ]);
    }

    onConditionChange(changedCondition: RuleCondition) {
        const changedConditions = this.ruleConditions.map(condition => {
            if (condition.id === changedCondition.id) {
                return changedCondition;
            }
            return condition;
        });
        this.ruleConditionsChange.emit(changedConditions);
    }

    onConditionRemove(removedCondition: RuleCondition) {
        const changedConditions = this.ruleConditions.filter(condition => {
            return condition.id !== removedCondition.id;
        });
        this.ruleConditionsChange.emit(changedConditions);
    }

    trackById(index: number, item: RuleCondition): string {
        return item.id;
    }

    // TODO (automation-rules): Try to remove id (needed by *ngFor?) since this implementation breaks when editing existing rules
    private generateNewCondition(): RuleCondition {
        return {
            id: ruleFormHelpers.uuid(),
            firstOperand: null,
            firstOperandValue: null,
            firstOperandTimeRange: TimeRange.Lifetime,
            operator: null,
            secondOperand: null,
            secondOperandValue: null,
            secondOperandTimeRange: TimeRange.Lifetime,
        };
    }
}
