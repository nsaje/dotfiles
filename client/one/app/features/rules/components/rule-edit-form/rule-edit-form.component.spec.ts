import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {RuleEditFormComponent} from './rule-edit-form.component';
import {RuleEditFormActionComponent} from '../rule-edit-form-action/rule-edit-form-action.component';
import {RuleEditFormConditionComponent} from '../rule-edit-form-condition/rule-edit-form-condition.component';
import {RuleEditFormConditionsComponent} from '../rule-edit-form-conditions/rule-edit-form-conditions.component';
import {RuleEditFormConditionModifierComponent} from '../rule-edit-form-condition-modifier/rule-edit-form-condition-modifier.component';
import {RuleEditFormNotificationComponent} from '../rule-edit-form-notification/rule-edit-form-notification.component';
import {RulesService} from '../../../../core/rules/services/rules.service';
import {RulesEndpoint} from '../../../../core/rules/services/rules.endpoint';
import {PublisherGroupsService} from '../../../../core/publisher-groups/services/publisher-groups.service';
import {PublisherGroupsEndpoint} from '../../../../core/publisher-groups/services/publisher-groups.endpoint';

describe('RuleEditFormComponent', () => {
    let component: RuleEditFormComponent;
    let fixture: ComponentFixture<RuleEditFormComponent>;
    let zemNavigationServiceStub: any;

    beforeEach(() => {
        zemNavigationServiceStub = {
            getActiveAccount: () => {
                return {
                    data: {
                        agencyId: '123',
                    },
                };
            },
        };
        TestBed.configureTestingModule({
            declarations: [
                RuleEditFormComponent,
                RuleEditFormActionComponent,
                RuleEditFormConditionComponent,
                RuleEditFormConditionsComponent,
                RuleEditFormConditionModifierComponent,
                RuleEditFormNotificationComponent,
            ],
            imports: [FormsModule, SharedModule],
            providers: [
                PublisherGroupsService,
                PublisherGroupsEndpoint,
                RulesService,
                RulesEndpoint,
                {
                    provide: 'zemNavigationNewService',
                    useValue: zemNavigationServiceStub,
                },
            ],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RuleEditFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
