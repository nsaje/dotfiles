import './rule-form-conditions.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {RuleCondition} from '../../types/rule-condition';
import * as clone from 'clone';

@Component({
    selector: 'zem-rule-form-conditions',
    templateUrl: './rule-form-conditions.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RuleFormConditionsComponent implements OnChanges {
    @Input()
    conditions: RuleCondition[];
    @Output()
    conditionsChange = new EventEmitter<RuleCondition[]>();

    items: RuleCondition[];

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.conditions) {
            this.items = clone(this.conditions);
        }
    }

    addCondition() {
        this.items.push(this.getNewCondition());
    }

    onConditionChange($event: RuleCondition, index: number) {
        this.items[index] = $event;
        this.conditionsChange.emit(clone(this.items));
    }

    onConditionRemove(index: number) {
        this.items.splice(index, 1);
        this.conditionsChange.emit(clone(this.items));
    }

    trackById(index: number, item: RuleCondition): string {
        return item.id;
    }

    private getNewCondition(): RuleCondition {
        const condition: RuleCondition = {
            id: this.uuid(),
            firstOperand: {
                property: null,
                value: null,
                modifier: {
                    timeRange: null,
                    valueModifier: null,
                },
            },
            operator: null,
            secondOperand: {
                property: null,
                value: null,
                modifier: {
                    timeRange: null,
                    valueModifier: {},
                },
            },
        };
        return condition;
    }

    private uuid(): string {
        return Math.floor((1 + Math.random()) * 0x10000)
            .toString(16)
            .substring(1);
    }
}
