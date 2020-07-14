import {ICellRendererParams} from 'ag-grid-community';
import {Rule} from '../../../../../core/rules/types/rule';

export interface RuleRunsOnRendererParams extends ICellRendererParams {
    data: Rule;
}
