import {ICellRendererParams} from 'ag-grid-community';
import {Rule} from '../../../../../core/rules/types/rule';
import {MappedRuleEntity} from '../../../types/mapped-rule-entity';

export interface RuleRunsOnRendererParams extends ICellRendererParams {
    data: Rule;
    getEntities: (rule: Rule) => MappedRuleEntity[];
}
