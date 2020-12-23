import './item-scope-cell.component.less';

import {Component} from '@angular/core';
import {ICellRendererAngularComp} from 'ag-grid-angular';
import * as commonHelpers from '../../../../../helpers/common.helpers';
import {ItemScopeRendererParams} from './types/item-scope.renderer-params';
import {ItemScopeState} from './item-scope-cell.constants';

@Component({
    templateUrl: './item-scope-cell.component.html',
})
export class ItemScopeCellComponent<T> implements ICellRendererAngularComp {
    params: ItemScopeRendererParams<T>;
    item: T;

    itemScopeState: ItemScopeState;
    entityName: string;
    canUseEntityLink: boolean;
    entityLink: string;

    private agencyIdField: string;
    private agencyNameField: string;
    private accountIdField: string;
    private accountNameField: string;

    agInit(params: ItemScopeRendererParams<T>) {
        this.params = params;
        this.item = params.data;

        this.agencyIdField = commonHelpers.getValueOrDefault(
            this.params.agencyIdField,
            'agencyId'
        );
        this.agencyNameField = commonHelpers.getValueOrDefault(
            this.params.agencyNameField,
            'agencyName'
        );
        this.accountIdField = commonHelpers.getValueOrDefault(
            this.params.accountIdField,
            'accountId'
        );
        this.accountNameField = commonHelpers.getValueOrDefault(
            this.params.accountNameField,
            'accountName'
        );

        this.itemScopeState = this.getItemScopeState(this.item);

        if (this.itemScopeState === ItemScopeState.AGENCY_SCOPE) {
            this.entityName = commonHelpers.getValueOrDefault(
                this.item[this.agencyNameField],
                'N/A'
            );
            this.canUseEntityLink = commonHelpers.getValueOrDefault(
                this.params.canUseAgencyLink,
                true
            );
            this.entityLink =
                commonHelpers.isDefined(this.params.getAgencyLink) &&
                this.params.getAgencyLink(this.item);
        } else if (this.itemScopeState === ItemScopeState.ACCOUNT_SCOPE) {
            this.entityName = commonHelpers.getValueOrDefault(
                this.item[this.accountNameField],
                'N/A'
            );
            this.canUseEntityLink = commonHelpers.getValueOrDefault(
                this.params.canUseAccountLink,
                true
            );
            this.entityLink =
                commonHelpers.isDefined(this.params.getAccountLink) &&
                this.params.getAccountLink(this.item);
        }
    }

    refresh(params: ItemScopeRendererParams<T>): boolean {
        const agencyId = params.value.agencyId;
        const accountId = params.value.accountId;
        if (
            this.params.value.agencyId !== agencyId ||
            this.params.value.accountId !== accountId
        ) {
            return false;
        }
        return true;
    }

    private getItemScopeState(item: T): ItemScopeState {
        if (commonHelpers.isDefined(item[this.agencyIdField])) {
            return ItemScopeState.AGENCY_SCOPE;
        } else if (commonHelpers.isDefined(item[this.accountIdField])) {
            return ItemScopeState.ACCOUNT_SCOPE;
        }
        return null;
    }
}
