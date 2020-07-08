import './rules-histories-filters.component.less';
import {
    Input,
    Component,
    ChangeDetectionStrategy,
    Output,
    EventEmitter,
} from '@angular/core';
import {RuleHistoryFilterState} from '../../types/rule-history-filter-state';
import {Rule} from '../../../../core/rules/types/rule';
import {AdGroup} from '../../../../core/entities/types/ad-group/ad-group';

@Component({
    selector: 'zem-rules-histories-filters',
    templateUrl: './rules-histories-filters.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RulesHistoriesFiltersComponent {
    @Input()
    selectedFilters: RuleHistoryFilterState;
    @Input()
    rules: Rule[] = [];
    @Input()
    adGroups: AdGroup[] = [];
    @Output()
    searchRules: EventEmitter<string> = new EventEmitter<string>();
    @Output()
    searchAdGroups: EventEmitter<string> = new EventEmitter<string>();
    @Output()
    filtersChange: EventEmitter<RuleHistoryFilterState> = new EventEmitter<
        RuleHistoryFilterState
    >();

    onRuleIdChange(ruleId: string | null) {
        this.filtersChange.emit({
            ...this.selectedFilters,
            ruleId: ruleId,
        });
    }

    onAdGroupIdChange(adGroupId: string | null) {
        this.filtersChange.emit({
            ...this.selectedFilters,
            adGroupId: adGroupId,
        });
    }

    onStartDateChange(startDate: Date | null) {
        this.filtersChange.emit({
            ...this.selectedFilters,
            startDate: startDate,
        });
    }

    onEndDateChange(endDate: Date | null) {
        this.filtersChange.emit({
            ...this.selectedFilters,
            endDate: endDate,
        });
    }
}
