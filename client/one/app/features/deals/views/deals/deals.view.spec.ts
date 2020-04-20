import {TestBed, ComponentFixture} from '@angular/core/testing';
import {RouterTestingModule} from '@angular/router/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DealsView} from './deals.view';
import {DealsStore} from '../../services/deals-store/deals.store';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {SourcesEndpoint} from '../../../../core/sources/services/sources.endpoint';
import {DealsEndpoint} from '../../../../core/deals/services/deals.endpoint';
import {ConnectionsListComponent} from '../../components/connections-list/connections-list.component';
import {DealsActionsComponent} from '../../components/deals-actions/deals-actions.component';
import {noop} from 'rxjs';
import {ActivatedRoute} from '@angular/router';
import {AccountEndpoint} from '../../../../core/entities/services/account/account.endpoint';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {EntitiesUpdatesService} from '../../../../core/entities/services/entities-updates.service';

describe('DealsView', () => {
    let component: DealsView;
    let fixture: ComponentFixture<DealsView>;

    let zemPermissionsStub: any;

    beforeEach(() => {
        zemPermissionsStub = {
            hasAgencyScope: () => noop,
            hasPermission: () => noop,
        };

        TestBed.configureTestingModule({
            declarations: [
                DealsView,
                ConnectionsListComponent,
                DealsActionsComponent,
            ],
            imports: [
                FormsModule,
                SharedModule,
                RouterTestingModule.withRoutes([]),
            ],
            providers: [
                DealsStore,
                DealsService,
                DealsEndpoint,
                {
                    provide: 'zemPermissions',
                    useValue: zemPermissionsStub,
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

                AccountService,
                AccountEndpoint,
                EntitiesUpdatesService,
            ],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DealsView);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
