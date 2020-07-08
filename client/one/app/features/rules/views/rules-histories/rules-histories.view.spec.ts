import {RulesHistoriesView} from './rules-histories.view';
import {ComponentFixture, TestBed} from '@angular/core/testing';
import {noop} from 'rxjs';
import {RulesHistoriesGridComponent} from '../../components/rules-histories-grid/rules-histories-grid.component';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {RouterTestingModule} from '@angular/router/testing';
import {RulesHistoriesStore} from '../../services/rules-histories-store/rules-histories.store';
import {RulesService} from '../../../../core/rules/services/rules.service';
import {RulesEndpoint} from '../../../../core/rules/services/rules.endpoint';
import {ActivatedRoute} from '@angular/router';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {AccountEndpoint} from '../../../../core/entities/services/account/account.endpoint';
import {EntitiesUpdatesService} from '../../../../core/entities/services/entities-updates.service';
import {RulesHistoriesFiltersComponent} from '../../components/rules-histories-filters/rules-histories-filters.component';
import {AdGroupService} from '../../../../core/entities/services/ad-group/ad-group.service';
import {AdGroupEndpoint} from '../../../../core/entities/services/ad-group/ad-group.endpoint';

describe('RulesView', () => {
    let component: RulesHistoriesView;
    let fixture: ComponentFixture<RulesHistoriesView>;

    let zemPermissionsStub: any;

    beforeEach(() => {
        zemPermissionsStub = {
            hasAgencyScope: () => noop,
            hasPermission: () => noop,
        };

        TestBed.configureTestingModule({
            declarations: [
                RulesHistoriesView,
                RulesHistoriesGridComponent,
                RulesHistoriesFiltersComponent,
            ],
            imports: [
                FormsModule,
                SharedModule,
                RouterTestingModule.withRoutes([]),
            ],
            providers: [
                RulesHistoriesStore,
                RulesService,
                RulesEndpoint,
                AdGroupService,
                AdGroupEndpoint,
                {
                    provide: 'zemPermissions',
                    useValue: zemPermissionsStub,
                },
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
        fixture = TestBed.createComponent(RulesHistoriesView);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
