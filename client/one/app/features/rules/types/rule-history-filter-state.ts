export interface RuleHistoryFilterState {
    ruleId: string | null;
    adGroupId: string | null;
    startDate: Date | null;
    endDate: Date | null;
    showEntriesWithoutChanges: boolean | null;
}
