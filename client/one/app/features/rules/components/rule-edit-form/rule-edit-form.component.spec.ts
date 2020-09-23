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
import {AccountService} from '../../../../core/entities/services/account/account.service';
import {AccountEndpoint} from '../../../../core/entities/services/account/account.endpoint';
import {EntitiesUpdatesService} from '../../../../core/entities/services/entities-updates.service';
import {CampaignService} from '../../../../core/entities/services/campaign/campaign.service';
import {CampaignEndpoint} from '../../../../core/entities/services/campaign/campaign.endpoint';
import {AdGroupService} from '../../../../core/entities/services/ad-group/ad-group.service';
import {AdGroupEndpoint} from '../../../../core/entities/services/ad-group/ad-group.endpoint';
import {AuthStore} from '../../../../core/auth/services/auth.store';
import {ConversionPixelsEndpoint} from '../../../../core/conversion-pixels/services/conversion-pixels.endpoint';
import {ConversionPixelsService} from '../../../../core/conversion-pixels/services/conversion-pixels.service';
import {RuleEditFormConditionConversionPixelComponent} from '../rule-edit-form-condition-conversion-pixel/rule-edit-form-condition-conversion-pixel.component';

describe('RuleEditFormComponent', () => {
    let component: RuleEditFormComponent;
    let fixture: ComponentFixture<RuleEditFormComponent>;
    let authStoreStub: jasmine.SpyObj<AuthStore>;

    beforeEach(() => {
        authStoreStub = jasmine.createSpyObj(AuthStore.name, [
            'hasAgencyScope',
        ]);

        TestBed.configureTestingModule({
            declarations: [
                RuleEditFormComponent,
                RuleEditFormActionComponent,
                RuleEditFormConditionComponent,
                RuleEditFormConditionsComponent,
                RuleEditFormConditionModifierComponent,
                RuleEditFormNotificationComponent,
                RuleEditFormConditionConversionPixelComponent,
            ],
            imports: [FormsModule, SharedModule],
            providers: [
                PublisherGroupsService,
                PublisherGroupsEndpoint,
                ConversionPixelsService,
                ConversionPixelsEndpoint,
                RulesService,
                RulesEndpoint,
                AccountService,
                AccountEndpoint,
                CampaignService,
                CampaignEndpoint,
                AdGroupService,
                AdGroupEndpoint,
                EntitiesUpdatesService,
                {
                    provide: AuthStore,
                    useValue: authStoreStub,
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
