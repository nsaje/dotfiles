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
import {RulesActionsComponent} from '../../components/rules-actions/rules-actions.component';
import {RuleEditFormComponent} from '../../components/rule-edit-form/rule-edit-form.component';
import {RuleEditFormActionComponent} from '../../components/rule-edit-form-action/rule-edit-form-action.component';
import {RuleEditFormConditionComponent} from '../../components/rule-edit-form-condition/rule-edit-form-condition.component';
import {RuleEditFormConditionModifierComponent} from '../../components/rule-edit-form-condition-modifier/rule-edit-form-condition-modifier.component';
import {RuleEditFormNotificationComponent} from '../../components/rule-edit-form-notification/rule-edit-form-notification.component';
import {RuleEditFormConditionsComponent} from '../../components/rule-edit-form-conditions/rule-edit-form-conditions.component';
import {AuthStore} from '../../../../core/auth/services/auth.store';

describe('RulesView', () => {
    let component: RulesView;
    let fixture: ComponentFixture<RulesView>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;

    beforeEach(() => {
        authStoreStub = jasmine.createSpyObj(AuthStore.name, [
            'hasAgencyScope',
            'hasPermission',
        ]);

        TestBed.configureTestingModule({
            declarations: [
                RulesView,
                RulesGridComponent,
                RulesActionsComponent,
                RuleEditFormComponent,
                RuleEditFormActionComponent,
                RuleEditFormConditionComponent,
                RuleEditFormConditionModifierComponent,
                RuleEditFormNotificationComponent,
                RuleEditFormConditionsComponent,
            ],
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
                    provide: AuthStore,
                    useValue: authStoreStub,
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
