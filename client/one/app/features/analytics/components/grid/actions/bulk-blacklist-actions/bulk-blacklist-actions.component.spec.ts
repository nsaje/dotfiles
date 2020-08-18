import {
    ComponentFixture,
    fakeAsync,
    TestBed,
    tick,
} from '@angular/core/testing';
import {SharedModule} from '../../../../../../shared/shared.module';
import {BulkBlacklistActionsComponent} from './bulk-blacklist-actions.component';
import {OnChanges, SimpleChange, SimpleChanges} from '@angular/core';
import {PublisherInfo} from '../../../../../../core/publishers/types/publisher-info';
import {PublishersModule} from '../../../../../../core/publishers/publishers.module';
import {
    PublisherBlacklistLevel,
    PublisherTargetingStatus,
} from '../../../../../../app.constants';
import {BulkBlacklistActionsStore} from './services/bulk-blacklist-actions.store';
import {AuthStore} from '../../../../../../core/auth/services/auth.store';

describe('BulkBlacklistActionsComponent', () => {
    let storeStub: jasmine.SpyObj<BulkBlacklistActionsStore>;
    let component: BulkBlacklistActionsComponent;
    let fixture: ComponentFixture<BulkBlacklistActionsComponent>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;

    let hasGlobalBlacklistPermission: boolean;

    const selectedPublisherRows: PublisherInfo[] = [
        {
            sourceId: 12,
            sourceSlug: '12',
            publisher: 'www.zemanta.com',
        },
        {
            sourceId: 34,
            sourceSlug: '34',
            publisher: 'www.outbrain.com',
        },
    ];

    const reportedPlacementRows: PublisherInfo[] = [
        {
            sourceId: 12,
            sourceSlug: '12',
            publisher: 'www.zemanta.com',
            placement: '1234-5678',
        },
        {
            sourceId: 34,
            sourceSlug: '34',
            publisher: 'www.outbrain.com',
            placement: '2345-6789',
        },
    ];

    const notReportedPlacementRows: PublisherInfo[] = [
        {
            sourceId: 56,
            sourceSlug: '56',
            publisher: 'www.taboola.com',
            placement: 'Not reported',
        },
    ];

    const selectedPlacementRows: PublisherInfo[] = [
        ...reportedPlacementRows,
        ...notReportedPlacementRows,
    ];

    function changeComponent<T extends OnChanges>(
        component: T,
        changes: Partial<T>
    ) {
        const simpleChanges: SimpleChanges = {};

        Object.keys(changes).forEach(changeKey => {
            component[changeKey] = changes[changeKey];
            simpleChanges[changeKey] = new SimpleChange(
                null,
                changes[changeKey],
                false
            );
        });
        component.ngOnChanges(simpleChanges);
    }

    beforeEach(() => {
        spyOn(window, 'confirm').and.returnValue(true);
        storeStub = jasmine.createSpyObj(BulkBlacklistActionsStore.name, [
            'updateBlacklistStatuses',
        ]);
        storeStub.updateBlacklistStatuses.and.returnValue(
            new Promise<boolean>(resolve => {
                resolve(true);
            })
        );

        authStoreStub = jasmine.createSpyObj(AuthStore.name, ['hasPermission']);
        authStoreStub.hasPermission.and.callFake(permission => {
            if (
                permission ===
                'zemauth.can_access_global_publisher_blacklist_status'
            ) {
                return hasGlobalBlacklistPermission;
            } else {
                return true;
            }
        });
        TestBed.configureTestingModule({
            declarations: [BulkBlacklistActionsComponent],
            imports: [SharedModule, PublishersModule],
            providers: [
                {
                    provide: AuthStore,
                    useValue: authStoreStub,
                },
            ],
        })
            .overrideComponent(BulkBlacklistActionsComponent, {
                set: {
                    providers: [
                        {
                            provide: BulkBlacklistActionsStore,
                            useValue: storeStub,
                        },
                    ],
                },
            })
            .compileComponents();
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BulkBlacklistActionsComponent);
        component = fixture.componentInstance;
        hasGlobalBlacklistPermission = true;
        component.ngOnInit();
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should disable dropdowns if no rows are selected', () => {
        changeComponent(component, {selectedRows: []});
        expect(component.dropdownsDisabled).toBeTrue();
    });

    it('should enable dropdowns if publisher rows are selected', () => {
        changeComponent(component, {selectedRows: selectedPublisherRows});
        expect(component.dropdownsDisabled).toBeFalse();
    });

    it('should enable dropdowns if placement rows are selected', () => {
        changeComponent(component, {selectedRows: selectedPlacementRows});
        expect(component.dropdownsDisabled).toBeFalse();
    });

    it('should disable dropdowns if only not-reported placements are selected', () => {
        changeComponent(component, {selectedRows: notReportedPlacementRows});
        expect(component.dropdownsDisabled).toBeTrue();
    });

    it('should display all allowed actions', () => {
        expect(component.blacklistActions.map(x => x.name)).toEqual([
            'Add to',
            'Remove from',
        ]);
    });

    it('should not display any levels if no IDs are supplied and user has no global blacklist permission', () => {
        hasGlobalBlacklistPermission = false;
        component.ngOnInit();
        expect(component.blacklistLevels.map(x => x.name)).toEqual([]);
    });

    it('should only display global level if no IDs are supplied and user has global blacklist permission', () => {
        expect(component.blacklistLevels.map(x => x.name)).toEqual(['global']);
    });

    it('should also display ad group level if an adGroupId is supplied', () => {
        changeComponent(component, {adGroupId: 1});
        expect(component.blacklistLevels.map(x => x.name)).toEqual([
            'ad group',
            'global',
        ]);
    });

    it('should also display campaign level if an campaignId is supplied', () => {
        changeComponent(component, {campaignId: 1});
        expect(component.blacklistLevels.map(x => x.name)).toEqual([
            'campaign',
            'global',
        ]);
    });

    it('should also display account level if an accountId is supplied', () => {
        changeComponent(component, {accountId: 1});
        expect(component.blacklistLevels.map(x => x.name)).toEqual([
            'account',
            'global',
        ]);
    });

    it('should display all levels with supplied IDs', () => {
        changeComponent(component, {adGroupId: 1, campaignId: 2, accountId: 3});
        expect(component.blacklistLevels.map(x => x.name)).toEqual([
            'ad group',
            'campaign',
            'account',
            'global',
        ]);

        hasGlobalBlacklistPermission = false;
        changeComponent(component, {adGroupId: 1, campaignId: 2, accountId: 3});
        expect(component.blacklistLevels.map(x => x.name)).toEqual([
            'ad group',
            'campaign',
            'account',
        ]);
    });

    it('should call updateBlacklistStatuses for ad group with the ad group ID', fakeAsync(() => {
        changeComponent(component, {
            selectedRows: selectedPublisherRows,
            adGroupId: 1,
            campaignId: 2,
            accountId: 3,
        });
        component.dropdowns = [];

        component.updateBlacklistStatuses(
            PublisherTargetingStatus.BLACKLISTED,
            PublisherBlacklistLevel.ADGROUP
        );

        tick();

        expect(storeStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            selectedPublisherRows,
            PublisherTargetingStatus.BLACKLISTED,
            PublisherBlacklistLevel.ADGROUP,
            1
        );
    }));

    it('should call updateBlacklistStatuses for campaign with the campaign ID', fakeAsync(() => {
        changeComponent(component, {
            selectedRows: selectedPublisherRows,
            adGroupId: 1,
            campaignId: 2,
            accountId: 3,
        });
        component.dropdowns = [];

        component.updateBlacklistStatuses(
            PublisherTargetingStatus.BLACKLISTED,
            PublisherBlacklistLevel.CAMPAIGN
        );

        tick();

        expect(storeStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            selectedPublisherRows,
            PublisherTargetingStatus.BLACKLISTED,
            PublisherBlacklistLevel.CAMPAIGN,
            2
        );
    }));

    it('should call updateBlacklistStatuses for account with the account ID', fakeAsync(() => {
        changeComponent(component, {
            selectedRows: selectedPublisherRows,
            adGroupId: 1,
            campaignId: 2,
            accountId: 3,
        });
        component.dropdowns = [];

        component.updateBlacklistStatuses(
            PublisherTargetingStatus.BLACKLISTED,
            PublisherBlacklistLevel.ACCOUNT
        );

        tick();

        expect(storeStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            selectedPublisherRows,
            PublisherTargetingStatus.BLACKLISTED,
            PublisherBlacklistLevel.ACCOUNT,
            3
        );
    }));

    it('should call updateBlacklistStatuses for global without an ID', fakeAsync(() => {
        changeComponent(component, {
            selectedRows: selectedPublisherRows,
            adGroupId: 1,
            campaignId: 2,
            accountId: 3,
        });
        component.dropdowns = [];

        component.updateBlacklistStatuses(
            PublisherTargetingStatus.BLACKLISTED,
            PublisherBlacklistLevel.GLOBAL
        );

        tick();

        expect(storeStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            selectedPublisherRows,
            PublisherTargetingStatus.BLACKLISTED,
            PublisherBlacklistLevel.GLOBAL,
            undefined
        );
    }));

    it('should not send not-reported placements to service', fakeAsync(() => {
        changeComponent(component, {
            selectedRows: selectedPlacementRows,
            adGroupId: 1,
            campaignId: 2,
            accountId: 3,
        });
        component.dropdowns = [];

        component.updateBlacklistStatuses(
            PublisherTargetingStatus.BLACKLISTED,
            PublisherBlacklistLevel.ADGROUP
        );

        tick();

        expect(storeStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            reportedPlacementRows, // Important: this is not the same value that we used for selectedRows
            PublisherTargetingStatus.BLACKLISTED,
            PublisherBlacklistLevel.ADGROUP,
            1
        );
    }));
});
