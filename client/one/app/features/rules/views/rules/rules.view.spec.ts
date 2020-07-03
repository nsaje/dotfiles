import {TestBed, ComponentFixture} from '@angular/core/testing';
import {RouterTestingModule} from '@angular/router/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {noop} from 'rxjs';
import {ActivatedRoute} from '@angular/router';
import {AccountEndpoint} from '../../../../core/entities/services/account/account.endpoint';
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {EntitiesUpdatesService} from '../../../../core/entities/services/entities-updates.service';
import {RulesView} from './rules.view';
import {RulesService} from '../../../../core/rules/services/rules.service';
import {RulesEndpoint} from '../../../../core/rules/services/rules.endpoint';
import {RulesStore} from '../../services/rules-store/rules.store';
import {RulesGridComponent} from '../../components/rules-grid/rules-grid.component';

describe('RulesView', () => {
    let component: RulesView;
    let fixture: ComponentFixture<RulesView>;

    let zemPermissionsStub: any;

    beforeEach(() => {
        zemPermissionsStub = {
            hasAgencyScope: () => noop,
            hasPermission: () => noop,
        };

        TestBed.configureTestingModule({
            declarations: [RulesView, RulesGridComponent],
            imports: [
                FormsModule,
                SharedModule,
                RouterTestingModule.withRoutes([]),
            ],
            providers: [
                RulesStore,
                RulesService,
                RulesEndpoint,
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
        fixture = TestBed.createComponent(RulesView);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
