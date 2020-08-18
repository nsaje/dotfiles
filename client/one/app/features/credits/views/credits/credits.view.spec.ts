import {TestBed, ComponentFixture} from '@angular/core/testing';
import {RouterTestingModule} from '@angular/router/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CreditsView} from './credits.view';
import {CreditsStore} from '../../services/credits-store/credits.store';
import {CreditsService} from '../../../../core/credits/services/credits.service';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {SourcesEndpoint} from '../../../../core/sources/services/sources.endpoint';
import {CreditsEndpoint} from '../../../../core/credits/services/credits.endpoint';
import {ActivatedRoute} from '@angular/router';
import {AccountEndpoint} from '../../../../core/entities/services/account/account.endpoint';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {EntitiesUpdatesService} from '../../../../core/entities/services/entities-updates.service';
import {CreditsGridComponent} from '../../components/credits-grid/credits-grid.component';
import {CreditActionsCellComponent} from '../../components/credits-grid/components/credit-actions-cell/credit-actions-cell.component';
import {RefundActionsCellComponent} from '../../components/credits-grid/components/refund-actions-cell/refund-actions-cell.component';
import {CreditEditFormComponent} from '../../components/credit-edit-form/credit-edit-form.component';
import {CreditsTotalsComponent} from '../../components/credits-totals/credits-totals.component';
import {CampaignBudgetsGridComponent} from '../../components/campaign-budgets-grid/campaign-budgets-grid.component';
import {RefundFormComponent} from '../../components/refund-form/refund-form.component';
import {RefundsGridComponent} from '../../components/refunds-grid/refunds-grid.component';
import {AuthStore} from '../../../../core/auth/services/auth.store';

describe('CreditsView', () => {
    let component: CreditsView;
    let fixture: ComponentFixture<CreditsView>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;

    beforeEach(() => {
        authStoreStub = jasmine.createSpyObj(AuthStore.name, [
            'hasAgencyScope',
            'hasPermission',
        ]);

        TestBed.configureTestingModule({
            declarations: [
                CreditsView,
                CreditsGridComponent,
                CreditEditFormComponent,
                CreditsTotalsComponent,
                CampaignBudgetsGridComponent,
                CreditActionsCellComponent,
                RefundActionsCellComponent,
                RefundFormComponent,
                RefundsGridComponent,
            ],
            imports: [
                FormsModule,
                SharedModule,
                RouterTestingModule.withRoutes([]),
            ],
            providers: [
                CreditsStore,
                CreditsService,
                CreditsEndpoint,
                {
                    provide: AuthStore,
                    useValue: authStoreStub,
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
        fixture = TestBed.createComponent(CreditsView);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
