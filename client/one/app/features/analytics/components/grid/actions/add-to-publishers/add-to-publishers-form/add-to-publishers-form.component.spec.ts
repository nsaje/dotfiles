import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../../../../shared/shared.module';
import {CoreModule} from '../../../../../../../core/core.module';
import {AddToPublishersFormComponent} from './add-to-publishers-form.component';
import {PublisherGroup} from '../../../../../../../core/publisher-groups/types/publisher-group';

describe('AddToPublishersFormComponent', () => {
    let component: AddToPublishersFormComponent;
    let fixture: ComponentFixture<AddToPublishersFormComponent>;
    let mockedPublisherGroups: PublisherGroup[];

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [AddToPublishersFormComponent],
            imports: [FormsModule, SharedModule, CoreModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(AddToPublishersFormComponent);
        component = fixture.componentInstance;

        mockedPublisherGroups = [
            {
                id: '10000000',
                name: 'something.com',
                accountId: '525',
                agencyId: null,
                includeSubdomains: false,
                implicit: false,
                size: 3,
                modifiedDt: new Date(),
                createdDt: new Date(),
                type: 'Blacklist',
                level: 'Campaign',
                levelName: 'Test campaign',
                levelId: 123456,
                entries: undefined,
            },
            {
                id: '10000001',
                name: 'test-group.com',
                accountId: '525',
                agencyId: null,
                includeSubdomains: false,
                implicit: false,
                size: 2,
                modifiedDt: new Date(),
                createdDt: new Date(),
                type: null,
                level: null,
                levelName: '',
                levelId: null,
                entries: undefined,
            },
            {
                id: '10000002',
                name: 'hmm.si',
                accountId: '525',
                agencyId: null,
                includeSubdomains: false,
                implicit: false,
                size: 2,
                modifiedDt: new Date(),
                createdDt: new Date(),
                type: null,
                level: null,
                levelName: '',
                levelId: null,
                entries: undefined,
            },
        ];
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly emit the selected publisher group', () => {
        component.availablePublisherGroups = mockedPublisherGroups;
        spyOn(component.publisherGroupSelected, 'emit');

        component.selectPublisherGroup('10000001');

        expect(component.publisherGroupSelected.emit).toHaveBeenCalledWith(
            mockedPublisherGroups[1]
        );
    });
});
