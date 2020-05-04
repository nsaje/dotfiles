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

describe('AddToPublishersActionComponent', () => {
    let component: AddToPublishersActionComponent;
    let fixture: ComponentFixture<AddToPublishersActionComponent>;
    let mockedPublisherRows: PublisherInfo[];
    let storeStub: jasmine.SpyObj<AddToPublishersActionStore>;

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

        mockedPublisherRows = [
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

        component.accountId = 123;
        component.selectedRows = mockedPublisherRows;
        component.addToPublishersModal = {
            close: () => {
                return;
            },
        } as any;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly trigger a search on the service', () => {
        component.search('test');

        expect(storeStub.search).toHaveBeenCalledWith('123', 'test');
    });

    it('should correctly save changes to the service', fakeAsync(() => {
        component.save();

        tick();

        expect(storeStub.save).toHaveBeenCalledWith('123', mockedPublisherRows);
    }));

    it('should reset the store state when the window closes', () => {
        component.close();

        expect(storeStub.reset).toHaveBeenCalled();
    });
});
