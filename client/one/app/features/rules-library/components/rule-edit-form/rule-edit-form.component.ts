import './rule-edit-form.component.less';

import {Component, ChangeDetectionStrategy, OnInit, Input} from '@angular/core';
import {RuleEditFormStore} from './services/rule-edit-form.store';
import {EntityType} from '../../../../app.constants';
import {RuleActionType} from '../../rules-library.constants';
import {RULE_DIMENSIONS, TIME_RANGES} from '../../rules-library.config';

@Component({
    selector: 'zem-rule-edit-form',
    templateUrl: './rule-edit-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [RuleEditFormStore],
})
export class RuleEditFormComponent implements OnInit {
    @Input()
    entityId: string;
    @Input()
    entityType: EntityType;

    title: string = '';
    RuleActionType = RuleActionType;
    availableDimensions = RULE_DIMENSIONS;
    availableTimeRanges = TIME_RANGES;

    constructor(public store: RuleEditFormStore) {}

    ngOnInit(): void {
        // TODO (automation-rules): Remove when entity selector gets implemented
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