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
import {RuleActionType, TimeRange} from './rule-form.constants';
import {RULE_DIMENSIONS} from './rule-form.config';

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
    @Output()
    ruleChange = new EventEmitter<any>();

    title: string = '';
    RuleActionType = RuleActionType;
    availableDimensions = RULE_DIMENSIONS;
    availableTimeRanges: any[] = [
        {
            name: 'Yesterday',
            value: TimeRange.Yesterday,
        },
        {
            name: 'Last 3 days',
            value: TimeRange.LastThreeDays,
        },
        {
            name: 'Last 7 days',
            value: TimeRange.LastSevenDays,
        },
        {
            name: 'Lifetime',
            value: TimeRange.Lifetime,
        },
    ];

    constructor(public store: RuleFormStore) {}

    ngOnInit(): void {
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
