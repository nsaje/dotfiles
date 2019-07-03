import './rule-form-conditions.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {RuleCondition} from '../../types/rule-condition';
import * as ruleFormHelpers from '../../helpers/rule-form.helpers';
import {RuleConditionConfig} from '../../types/rule-condition-config';
import {TimeRange} from '../../rule-form.constants';

@Component({
    selector: 'zem-rule-form-conditions',
    templateUrl: './rule-form-conditions.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleFormConditionsComponent {
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

    // PRTODO (jurebajt): Try to remove id (needed by *ngFor?) since this implementation breaks when editing existing rules
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
