import './styles/settings.less';
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
import {CampaignGoalEditFormComponent} from './components/campaign-goal-edit-form/campaign-goal-edit-form.component';
import {CampaignPerformanceTrackingComponent} from './components/campaign-performance-tracking/campaign-performance-tracking.component';
import {MediaSourcesComponent} from './components/media-sources/media-sources.component';

// DEMO
import {RuleActionsComponent} from './components/rule-actions/rule-actions.component';
import {RuleFormComponent} from './components/rule-form/rule-form.component';
import {RuleFormActionComponent} from './components/rule-form/components/rule-form-action/rule-form-action.component';
import {RuleFormNotificationComponent} from './components/rule-form/components/rule-form-notification/rule-form-notification.component';
import {RuleFormConditionsComponent} from './components/rule-form/components/rule-form-conditions/rule-form-conditions.component';
import {RuleFormConditionComponent} from './components/rule-form/components/rule-form-condition/rule-form-condition.component';
import {RuleFormConditionModifierComponent} from './components/rule-form/components/rule-form-condition-modifier/rule-form-condition-modifier.component';
import {CampaignBudgetsOverviewComponent} from './components/campaign-budgets-overview/campaign-budgets-overview.component';
import {CampaignBudgetsListComponent} from './components/campaign-budgets-list/campaign-budgets-list.component';
import {CampaignBudgetEditFormComponent} from './components/campaign-budget-edit-form/campaign-budget-edit-form.component';
import {CampaignBudgetOptimizationComponent} from './components/campaign-budget-optimization/campaign-budget-optimization.component';

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
        CampaignGoalEditFormComponent,
        CampaignBudgetsOverviewComponent,
        CampaignBudgetsListComponent,
        CampaignPerformanceTrackingComponent,
        CampaignBudgetEditFormComponent,
        CampaignBudgetOptimizationComponent,
        MediaSourcesComponent,

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
        DaypartingSettingComponent,
        RuleActionsComponent,
    ],
})
export class EntityManagerModule {}
