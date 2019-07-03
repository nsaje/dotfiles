import './rule-form.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    OnInit,
    Input,
} from '@angular/core';
import {RuleFormStore} from './services/rule-form.store';
import {EntityType} from '../../../../app.constants';
import {RuleActionType} from './rule-form.constants';
import {RULE_DIMENSIONS, TIME_RANGES} from './rule-form.config';

@Component({
    selector: 'zem-rule-form',
    templateUrl: './rule-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [RuleFormStore],
})
export class RuleFormComponent implements OnInit {
    @Input()
    entityId: string;
    @Input()
    entityType: EntityType;

    title: string = '';
    RuleActionType = RuleActionType;
    availableDimensions = RULE_DIMENSIONS;
    availableTimeRanges = TIME_RANGES;

    constructor(public store: RuleFormStore) {}

    ngOnInit(): void {
        // PRTODO (jurebajt): Remove when entity selector gets implemented
        this.title = this.getTitle(this.entityId, this.entityType);
    }

    private getTitle(entityId: string, entityType: EntityType): string {
        if (entityType === EntityType.CAMPAIGN) {
            return `All ad groups of campaign ${entityId}`;
        } else if (entityType === EntityType.AD_GROUP) {
            return `Ad group ${entityId}`;
        }
        return 'NOT SUPPORTED';
    }
}
