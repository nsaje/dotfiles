import './rule-edit-form.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    Input,
    Output,
    EventEmitter,
    AfterViewInit,
    OnChanges,
} from '@angular/core';
import {RuleEditFormStore} from './services/rule-edit-form.store';
import {EntityType} from '../../../../app.constants';
import {RuleActionType} from '../../../../core/rules/rules.constants';
import {RULE_TARGET_TYPES, TIME_RANGES} from '../../rules.config';
import {RuleEditFormApi} from './types/rule-edit-form-api';
import {Rule} from '../../../../core/rules/types/rule';
import {EntitySelectorItem} from '../../../../shared/components/entity-selector/types/entity-selector-item';
import {map, distinctUntilChanged, takeUntil} from 'rxjs/operators';
import {Subject} from 'rxjs';

@Component({
    selector: 'zem-rule-edit-form',
    templateUrl: './rule-edit-form.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [RuleEditFormStore],
})
export class RuleEditFormComponent implements OnInit, AfterViewInit {
    @Input()
    agencyId: string | null = null;
    @Input()
    accountId: string | null = null;
    @Input()
    entityId: string;
    @Input()
    entityName: string;
    @Input()
    entityType: EntityType;
    @Input()
    rule: Partial<Rule>;
    @Output()
    componentReady = new EventEmitter<RuleEditFormApi>();

    title: string = '';
    RuleActionType = RuleActionType;
    availableTargetTypes = RULE_TARGET_TYPES;
    availableTimeRanges = TIME_RANGES;

    selectedRuleEntities: EntitySelectorItem[] = [];

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(public store: RuleEditFormStore) {}

    ngOnInit(): void {
        this.store.initStore(
            this.agencyId,
            this.accountId,
            this.rule,
            this.entityId,
            this.entityName,
            this.entityType
        );

        this.store.state$
            .pipe(
                map(state => state.rule.entities),
                distinctUntilChanged(),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(() => {
                this.selectedRuleEntities = this.store.getRuleEntitySelectorItems();
            });
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
}
