import './rule-edit-form-conditions.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    OnChanges,
    Output,
    EventEmitter,
    SimpleChanges,
} from '@angular/core';
import {RuleCondition} from '../../../../core/rules/types/rule-condition';
import * as ruleFormHelpers from '../rule-edit-form/helpers/rule-edit-form.helpers';
import {RuleConditionConfig} from '../../../../core/rules/types/rule-condition-config';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {FieldErrors} from '../../../../shared/types/field-errors';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';

@Component({
    selector: 'zem-rule-edit-form-conditions',
    templateUrl: './rule-edit-form-conditions.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleEditFormConditionsComponent implements OnChanges {
    @Input()
    ruleConditions: RuleCondition[];
    @Input()
    availableConditions: RuleConditionConfig[];
    @Input()
    ruleConditionsErrors: FieldErrors[];
    @Output()
    ruleConditionAdd = new EventEmitter<RuleCondition>();
    @Output()
    ruleConditionChange = new EventEmitter<ChangeEvent<RuleCondition>>();
    @Output()
    ruleConditionRemove = new EventEmitter<RuleCondition>();

    generalConditionsError: string;
    perConditionErrors: FieldErrors[] = [];

    addCondition() {
        this.ruleConditionAdd.emit(this.generateNewCondition());
    }

    ngOnChanges(changes: SimpleChanges) {
        if (
            changes.ruleConditionsErrors &&
            !arrayHelpers.isEmpty(this.ruleConditionsErrors)
        ) {
            this.perConditionErrors = [];
            this.generalConditionsError = '';
            if (typeof this.ruleConditionsErrors[0] === 'object') {
                this.perConditionErrors = this.ruleConditionsErrors;
            } else if (typeof this.ruleConditionsErrors[0] === 'string') {
                // typescript-disable-next-line TS2322
                this.generalConditionsError = this.ruleConditionsErrors[0];
            }
        }
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
                window: null,
                modifier: null,
            },
            value: {
                type: null,
                window: null,
                value: null,
            },
        };
    }
}
