import './rule-runs-on-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {RuleRunsOnRendererParams} from './types/rule-runs-on.renderer-params';
import {RuleEntity} from '../../../../core/rules/types/rule-entity';

@Component({
    templateUrl: './rule-runs-on-cell.component.html',
})
export class RuleRunsOnCellComponent implements ICellRendererAngularComp {
    params: RuleRunsOnRendererParams;

    adGroups: RuleEntity[];
    campaigns: RuleEntity[];
    accounts: RuleEntity[];

    entityType: 'Account' | 'Campaign' | 'Ad group';
    entityName: string;
    entityLink: string;

    agInit(params: RuleRunsOnRendererParams) {
        this.params = params;

        this.adGroups = params.data.entities.adGroups?.included;
        this.campaigns = params.data.entities.campaigns?.included;
        this.accounts = params.data.entities.accounts?.included;

        if (commonHelpers.isNotEmpty(this.adGroups)) {
            this.entityType = 'Ad group';
            this.entityName = this.adGroups[0].name;
            this.entityLink = this.getEntityLink(
                'adgroup',
                this.adGroups[0].id
            );
        } else if (commonHelpers.isNotEmpty(this.campaigns)) {
            this.entityType = 'Campaign';
            this.entityName = this.campaigns[0].name;
            this.entityLink = this.getEntityLink(
                'campaign',
                this.campaigns[0].id
            );
        } else if (commonHelpers.isNotEmpty(this.accounts)) {
            this.entityType = 'Account';
            this.entityName = this.accounts[0].name;
            this.entityLink = this.getEntityLink(
                'account',
                this.accounts[0].id
            );
        }
    }

    getEntityLink(entityType: string, entityId: string) {
        return `/v2/analytics/${entityType}/${entityId}`;
    }

    refresh(): boolean {
        return false;
    }
}
