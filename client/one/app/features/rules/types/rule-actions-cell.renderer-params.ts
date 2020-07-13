import {ICellRendererParams} from 'ag-grid-community';
import {RulesView} from '../views/rules/rules.view';
import {Rule} from '../../../core/rules/types/rule';

export interface RuleActionsCellRendererParams extends ICellRendererParams {
    context: {
        componentParent: RulesView;
    };
    data: Rule;
}
