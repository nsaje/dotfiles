import './rule-actions-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {Rule} from '../../../../core/rules/types/rule';
import {RuleActionsCellRendererParams} from '../../types/rule-actions-cell.renderer-params';

@Component({
    templateUrl: './rule-actions-cell.component.html',
})
export class RuleActionsCellComponent implements ICellRendererAngularComp {
    params: RuleActionsCellRendererParams;
    rule: Rule;
    isReadOnly: boolean;

    agInit(params: RuleActionsCellRendererParams) {
        this.params = params;
        this.rule = params.data;

        this.isReadOnly = this.params.context.componentParent.store.isReadOnly(
            this.rule
        );
    }

    removeRule() {
        this.params.context.componentParent.removeRule(this.rule);
    }

    openEditRuleModal() {
        this.params.context.componentParent.openEditRuleModal(this.rule);
    }

    refresh(): boolean {
        return false;
    }
}
