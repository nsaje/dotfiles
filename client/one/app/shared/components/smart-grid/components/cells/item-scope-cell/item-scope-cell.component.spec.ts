import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ItemScopeCellComponent} from './item-scope-cell.component';
import {ItemScopeRendererParams} from './types/item-scope.renderer-params';
import {ItemScopeState} from './item-scope-cell.constants';

interface ScopedItem {
    agencyId: string;
    agencyName: string;
    accountId: string;
    accountName: string;
}

describe('ObjectScopeCellComponent', () => {
    let component: ItemScopeCellComponent<ScopedItem>;
    let fixture: ComponentFixture<ItemScopeCellComponent<ScopedItem>>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ItemScopeCellComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent<ItemScopeCellComponent<ScopedItem>>(
            ItemScopeCellComponent
        );
        component = fixture.componentInstance;
    });

    it('should be correctly initialized with agency scope', () => {
        expect(component).toBeDefined();

        const scopedItem: ScopedItem = {
            agencyId: '123',
            agencyName: 'Test agency',
            accountId: null,
            accountName: null,
        };

        const params: Partial<ItemScopeRendererParams<ScopedItem>> = {
            data: scopedItem,
            getAgencyLink: item => {
                return `/admin/dash/agency/${item.agencyId}/change/`;
            },
        };

        component.agInit(params as any);

        expect(component.itemScopeState).toEqual(ItemScopeState.AGENCY_SCOPE);
        expect(component.entityName).toEqual(scopedItem.agencyName);
        expect(component.canUseEntityLink).toEqual(true);
        expect(component.entityLink).toEqual(
            `/admin/dash/agency/${scopedItem.agencyId}/change/`
        );
    });

    it('should be correctly initialized with account scope', () => {
        expect(component).toBeDefined();

        const scopedItem: ScopedItem = {
            agencyId: null,
            agencyName: null,
            accountId: '123',
            accountName: 'Test account',
        };

        const params: Partial<ItemScopeRendererParams<ScopedItem>> = {
            data: scopedItem,
            getAccountLink: item => {
                return `/v2/analytics/account/${item.accountId}`;
            },
        };

        component.agInit(params as any);

        expect(component.itemScopeState).toEqual(ItemScopeState.ACCOUNT_SCOPE);
        expect(component.entityName).toEqual(scopedItem.accountName);
        expect(component.canUseEntityLink).toEqual(true);
        expect(component.entityLink).toEqual(
            `/v2/analytics/account/${scopedItem.accountId}`
        );
    });
});
