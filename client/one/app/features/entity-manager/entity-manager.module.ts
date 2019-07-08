import './styles/settings.less';
import './styles/settings-form-group.less';
import './styles/settings-section.less';

import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {CampaignCreatorComponent} from './components/campaign-creator/campaign-creator.component';
import {CampaignCreatorModalComponent} from './components/campaign-creator-modal/campaign-creator-modal.component';
import {CampaignTypeSelectorComponent} from './components/campaign-type-selector/campaign-type-selector.component';
import {DaypartingSettingComponent} from './components/dayparting-setting/dayparting-setting.component';
import {EntitySettingsRouterOutlet} from './router-outlets/entity-settings/entity-settings.router-outlet';
import {AdGroupSettingsDrawerView} from './views/ad-group-settings-drawer/ad-group-settings-drawer.view';
import {CampaignSettingsDrawerView} from './views/campaign-settings-drawer/campaign-settings-drawer.view';
import {AccountSettingsDrawerView} from './views/account-settings-drawer/account-settings-drawer.view';
import {TextSettingComponent} from './components/text-setting/text-setting.component';
import {TextAreaSettingComponent} from './components/textarea-setting/textarea-setting.component';
import {IntegerSettingComponent} from './components/integer-setting/integer-setting.component';
import {DecimalSettingComponent} from './components/decimal-setting/decimal-setting.component';
import {CurrencySettingComponent} from './components/currency-setting/currency-setting.component';
import {DateSettingComponent} from './components/date-setting/date-setting.component';
import {SelectSettingComponent} from './components/select-setting/select-setting.component';
import {CheckboxSettingComponent} from './components/checkbox-setting/checkbox-setting.component';
import {DeliveryTypeSettingComponent} from './components/delivery-type-setting/delivery-type-setting.component';
import {DemographicTargetingComponent} from './components/demographic-targeting/demographic-targeting.component';
import {GeoTargetingComponent} from './components/geo-targeting/geo-targeting.component';
import {ZipTargetingComponent} from './components/zip-targeting/zip-targeting.component';
import {DeviceTargetingSettingsComponent} from './components/device-targeting-settings/device-targeting-settings.component';
import {TrackingCodeSettingComponent} from './components/tracking-code-setting/tracking-code-setting.component';
import {TrackingPixelSettingComponent} from './components/tracking-pixel-setting/tracking-pixel-setting.component';
import {InterestTargetingComponent} from './components/interest-targeting/interest-targeting.component';
import {PublisherGroupTargetingComponent} from './components/publisher-groups-targeting/publisher-groups-targeting.component';
import {RetargetingComponent} from './components/retargeting/retargeting.component';
import {BiddingTypeSettingComponent} from './components/bidding-type-setting/bidding-type-setting.component';
import {AdvancedSettingsSectionComponent} from './components/advanced-settings-section/advanced-settings-section.component';
import {AdGroupAutopilotStateSettingComponent} from './components/ad-group-autopilot-state-setting/ad-group-autopilot-state-setting.component';
import {AdGroupRTBSourcesManagementSettingComponent} from './components/ad-group-rtb-sources-management-setting/ad-group-rtb-sources-management-setting.component';
import {HacksComponent} from './components/hacks/hacks.component';
import {DealsComponent} from './components/deals/deals.component';
import {SettingsDrawerFooterComponent} from './components/settings-drawer-footer/settings-drawer-footer.component';
import {SettingsDrawerHeaderComponent} from './components/settings-drawer-header/settings-drawer-header.component';
import {CampaignGoalsComponent} from './components/campaign-goals/campaign-goals.component';
import {CampaignGoalComponent} from './components/campaign-goal/campaign-goal.component';
import {CampaignGoalEditComponent} from './components/campaign-goal-edit/campaign-goal-edit.component';

// DEMO
import {RuleActionsComponent} from './components/rule-actions/rule-actions.component';
import {RuleFormComponent} from './components/rule-form/rule-form.component';
import {RuleFormActionComponent} from './components/rule-form/components/rule-form-action/rule-form-action.component';
import {RuleFormNotificationComponent} from './components/rule-form/components/rule-form-notification/rule-form-notification.component';
import {RuleFormConditionsComponent} from './components/rule-form/components/rule-form-conditions/rule-form-conditions.component';
import {RuleFormConditionComponent} from './components/rule-form/components/rule-form-condition/rule-form-condition.component';
import {RuleFormConditionModifierComponent} from './components/rule-form/components/rule-form-condition-modifier/rule-form-condition-modifier.component';

@NgModule({
    declarations: [
        EntitySettingsRouterOutlet,
        AccountSettingsDrawerView,
        CampaignSettingsDrawerView,
        AdGroupSettingsDrawerView,
        SettingsDrawerHeaderComponent,
        SettingsDrawerFooterComponent,
        CampaignCreatorComponent,
        CampaignCreatorModalComponent,
        CampaignTypeSelectorComponent,
        DaypartingSettingComponent,
        TextSettingComponent,
        TextAreaSettingComponent,
        IntegerSettingComponent,
        DecimalSettingComponent,
        CurrencySettingComponent,
        DateSettingComponent,
        SelectSettingComponent,
        CheckboxSettingComponent,
        DeliveryTypeSettingComponent,
        BiddingTypeSettingComponent,
        DemographicTargetingComponent,
        GeoTargetingComponent,
        ZipTargetingComponent,
        DeviceTargetingSettingsComponent,
        TrackingCodeSettingComponent,
        TrackingPixelSettingComponent,
        InterestTargetingComponent,
        PublisherGroupTargetingComponent,
        RetargetingComponent,
        AdvancedSettingsSectionComponent,
        AdGroupAutopilotStateSettingComponent,
        AdGroupRTBSourcesManagementSettingComponent,
        HacksComponent,
        DealsComponent,
        CampaignGoalsComponent,
        CampaignGoalComponent,
        CampaignGoalEditComponent,

        // DEMO
        RuleActionsComponent,
        RuleFormComponent,
        RuleFormActionComponent,
        RuleFormNotificationComponent,
        RuleFormConditionsComponent,
        RuleFormConditionComponent,
        RuleFormConditionModifierComponent,
    ],
    imports: [SharedModule],
    entryComponents: [
        EntitySettingsRouterOutlet,
        CampaignCreatorModalComponent,
        CampaignTypeSelectorComponent,
        DaypartingSettingComponent,
        RuleActionsComponent,
    ],
})
export class EntityManagerModule {}
