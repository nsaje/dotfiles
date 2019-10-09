import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DealsLibraryView} from './deals-library.view';
import {DealsLibraryStore} from '../../services/deals-library-store/deals-library.store';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {DealsEndpoint} from '../../../../core/deals/services/deals.endpoint';

describe('DealsLibraryView', () => {
    let component: DealsLibraryView;
    let fixture: ComponentFixture<DealsLibraryView>;
    let ajs$locationStub: any;

    beforeEach(() => {
        ajs$locationStub = {
            search: () => {},
        };
        TestBed.configureTestingModule({
            declarations: [DealsLibraryView],
            imports: [FormsModule, SharedModule],
            providers: [
                DealsLibraryStore,
                DealsService,
                DealsEndpoint,
                {
                    provide: 'ajs$location',
                    useValue: ajs$locationStub,
                },
            ],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DealsLibraryView);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
