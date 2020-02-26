import {TestBed, ComponentFixture} from '@angular/core/testing';
import {RouterTestingModule} from '@angular/router/testing';
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
import {noop} from 'rxjs';
import {ActivatedRoute} from '@angular/router';

describe('DealsLibraryView', () => {
    let component: DealsLibraryView;
    let fixture: ComponentFixture<DealsLibraryView>;
    let zemNavigationNewServiceStub: any;

    beforeEach(() => {
        zemNavigationNewServiceStub = {
            getEntityById: () => noop,
        };
        TestBed.configureTestingModule({
            declarations: [
                DealsLibraryView,
                ConnectionsListComponent,
                DealsLibraryActionsComponent,
            ],
            imports: [
                FormsModule,
                SharedModule,
                RouterTestingModule.withRoutes([]),
            ],
            providers: [
                DealsLibraryStore,
                DealsService,
                DealsEndpoint,
                {
                    provide: 'zemNavigationNewService',
                    useValue: zemNavigationNewServiceStub,
                },
                SourcesService,
                SourcesEndpoint,
                {
                    provide: ActivatedRoute,
                    useValue: {
                        snapshot: {
                            params: {},
                            data: {},
                        },
                    },
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
