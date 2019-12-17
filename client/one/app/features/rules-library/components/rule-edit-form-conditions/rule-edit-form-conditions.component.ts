import './rule-edit-form-conditions.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {RuleCondition} from '../../../../core/rules/types/rule-condition';
import * as ruleFormHelpers from '../rule-edit-form/helpers/rule-edit-form.helpers';
import {RuleConditionConfig} from '../../../../core/rules/types/rule-condition-config';
import {TimeRange} from '../../../../core/rules/rules.constants';
import {ChangeEvent} from '../../../../shared/types/change-event';

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
    ruleConditionAdd = new EventEmitter<RuleCondition>();
    @Output()
    ruleConditionChange = new EventEmitter<ChangeEvent<RuleCondition>>();
    @Output()
    ruleConditionRemove = new EventEmitter<RuleCondition>();

    addCondition() {
        this.ruleConditionAdd.emit(this.generateNewCondition());
    }

    onConditionChange(changedConditionEvent: ChangeEvent<RuleCondition>) {
        this.ruleConditionChange.emit(changedConditionEvent);
    }

    onConditionRemove(removedCondition: RuleCondition) {
        this.ruleConditionRemove.emit(removedCondition);
    }

    trackById(index: number, item: RuleCondition): string {
        return item.id;
    }

    // TODO (automation-rules): Try to remove id (needed by *ngFor?) since this implementation breaks when editing existing rules
    private generateNewCondition(): RuleCondition {
        return {
            id: ruleFormHelpers.uuid(),
            operator: null,
            metric: {
                type: null,
                window: TimeRange.Lifetime,
                modifier: null,
            },
            value: {
                type: null,
                window: TimeRange.Lifetime,
                value: null,
            },
        };
    }
}
