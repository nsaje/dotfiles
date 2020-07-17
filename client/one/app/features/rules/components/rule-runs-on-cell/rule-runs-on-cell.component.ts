import './rule-runs-on-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import {RuleRunsOnRendererParams} from './types/rule-runs-on.renderer-params';
import {MappedRuleEntity} from '../../types/mapped-rule-entity';

@Component({
    templateUrl: './rule-runs-on-cell.component.html',
})
export class RuleRunsOnCellComponent implements ICellRendererAngularComp {
    params: RuleRunsOnRendererParams;

    entities: MappedRuleEntity[] = [];

    agInit(params: RuleRunsOnRendererParams): void {
        this.params = params;
        this.entities = params.getEntities(params.data);
    }

    refresh(): boolean {
        return false;
    }
}
