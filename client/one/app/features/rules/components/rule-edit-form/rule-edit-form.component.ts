import './rule-edit-form.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    Input,
    Inject,
    Output,
    EventEmitter,
    AfterViewInit,
} from '@angular/core';
import {RuleEditFormStore} from './services/rule-edit-form.store';
import {EntityType} from '../../../../app.constants';
import {RuleActionType} from '../../../../core/rules/rules.constants';
import {RULE_TARGET_TYPES, TIME_RANGES} from '../../rules.config';
import {RuleEditFormApi} from './types/rule-edit-form-api';

@Component({
    selector: 'zem-rule-edit-form',
    templateUrl: './rule-edit-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [RuleEditFormStore],
})
export class RuleEditFormComponent implements OnInit, AfterViewInit {
    @Input()
    entityId: string;
    @Input()
    entityType: EntityType;
    @Input()
    agencyId: string;
    @Output()
    componentReady = new EventEmitter<RuleEditFormApi>();

    title: string = '';
    RuleActionType = RuleActionType;
    availableTargetTypes = RULE_TARGET_TYPES;
    availableTimeRanges = TIME_RANGES;

    constructor(
        public store: RuleEditFormStore,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    ngOnInit(): void {
        // TODO (automation-rules): Remove when entity selector gets implemented
        const activeAccount = this.zemNavigationNewService.getActiveAccount();
        const agencyId = (activeAccount.data || {}).agencyId;
        this.title = this.getTitle(this.entityId, this.entityType);
        this.store.initStore(agencyId, this.entityId);
    }

    ngAfterViewInit(): void {
        this.componentReady.emit({
            executeSave: this.saveEntity.bind(this),
        });
    }

    saveEntity(): Promise<void> {
        return this.store.saveEntity();
    }

    hasConditionsErrors() {
        return (
            this.store.state.fieldsErrors &&
            this.store.state.fieldsErrors.conditions &&
            this.store.state.fieldsErrors.conditions.length > 0
        );
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
