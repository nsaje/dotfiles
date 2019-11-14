import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DealsLibraryView} from './deals-library.view';
import {DealsLibraryStore} from '../../services/deals-library-store/deals-library.store';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {SourcesEndpoint} from '../../../../core/sources/services/sources.endpoint';
import {DealsEndpoint} from '../../../../core/deals/services/deals.endpoint';
import {ConnectionsListComponent} from '../../components/connections-list/connections-list.component';
import {DealsLibraryActionsComponent} from '../../components/deals-library-actions/deals-library-actions.component';

describe('DealsLibraryView', () => {
    let component: DealsLibraryView;
    let fixture: ComponentFixture<DealsLibraryView>;
    let ajs$locationStub: any;

    beforeEach(() => {
        ajs$locationStub = {
            search: () => '',
        };
        TestBed.configureTestingModule({
            declarations: [
                DealsLibraryView,
                ConnectionsListComponent,
                DealsLibraryActionsComponent,
            ],
            imports: [FormsModule, SharedModule],
            providers: [
                DealsLibraryStore,
                DealsService,
                DealsEndpoint,
                {
                    provide: 'ajs$location',
                    useValue: ajs$locationStub,
                },
                SourcesService,
                SourcesEndpoint,
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
