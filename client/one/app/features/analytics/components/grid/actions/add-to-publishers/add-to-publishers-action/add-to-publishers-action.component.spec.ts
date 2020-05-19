import {
    TestBed,
    ComponentFixture,
    tick,
    fakeAsync,
} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../../../../shared/shared.module';
import {CoreModule} from '../../../../../../../core/core.module';
import {AddToPublishersActionComponent} from './add-to-publishers-action.component';
import {AddToPublishersFormComponent} from '../add-to-publishers-form/add-to-publishers-form.component';
import {AddToPublishersActionStore} from './services/add-to-publishers-action.store';
import {PublisherInfo} from '../../../../../../../core/publishers/types/publisher-info';
import {OnChanges, SimpleChange, SimpleChanges} from '@angular/core';

describe('AddToPublishersActionComponent', () => {
    let component: AddToPublishersActionComponent;
    let fixture: ComponentFixture<AddToPublishersActionComponent>;
    let storeStub: jasmine.SpyObj<AddToPublishersActionStore>;

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
        storeStub = jasmine.createSpyObj(AddToPublishersActionStore.name, [
            'search',
            'save',
            'reset',
        ]);
        storeStub.save.and.returnValue(
            new Promise<void>(resolve => {
                resolve();
            })
        );
        TestBed.configureTestingModule({
            declarations: [
                AddToPublishersActionComponent,
                AddToPublishersFormComponent,
            ],
            imports: [FormsModule, SharedModule, CoreModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(AddToPublishersActionComponent);
        component = fixture.componentInstance;
        component.store = storeStub;

        component.accountId = 123;
        component.addToPublishersModal = {
            close: () => {
                return;
            },
        } as any;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should disable button if no rows are selected', () => {
        changeComponent(component, {selectedRows: []});
        expect(component.buttonDisabled).toBeTrue();
    });

    it('should enable button if publisher rows are selected', () => {
        changeComponent(component, {selectedRows: selectedPublisherRows});
        expect(component.buttonDisabled).toBeFalse();
    });

    it('should enable button if placement rows are selected', () => {
        changeComponent(component, {selectedRows: selectedPlacementRows});
        expect(component.buttonDisabled).toBeFalse();
    });

    it('should disable button if only not-reported placements are selected', () => {
        changeComponent(component, {selectedRows: notReportedPlacementRows});
        expect(component.buttonDisabled).toBeTrue();
    });

    it('should correctly trigger a search on the service', () => {
        component.search('test');

        expect(storeStub.search).toHaveBeenCalledWith('123', 'test');
    });

    it('should correctly save changes to the service', fakeAsync(() => {
        changeComponent(component, {selectedRows: selectedPublisherRows});
        component.save();

        tick();

        expect(storeStub.save).toHaveBeenCalledWith(
            '123',
            selectedPublisherRows
        );
    }));

    it('should not send not-reported placements to service', fakeAsync(() => {
        changeComponent(component, {selectedRows: selectedPlacementRows});
        component.save();

        tick();

        expect(storeStub.save).toHaveBeenCalledWith(
            '123',
            reportedPlacementRows // Important: this is not the same value that we used for selectedRows
        );
    }));

    it('should reset the store state when the window closes', () => {
        component.close();

        expect(storeStub.reset).toHaveBeenCalled();
    });
});
