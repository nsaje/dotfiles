import './styles/settings.less';
import './styles/settings-section.less';

import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {DaypartingSettingComponent} from './components/dayparting-setting/dayparting-setting.component';
import {EntitySettingsRouterOutlet} from './router-outlets/entity-settings/entity-settings.router-outlet';
import {AdGroupSettingsDrawerView} from './views/ad-group-settings-drawer/ad-group-settings-drawer.view';
import {CampaignSettingsDrawerView} from './views/campaign-settings-drawer/campaign-settings-drawer.view';
import {AccountSettingsDrawerView} from './views/account-settings-drawer/account-settings-drawer.view';
import {DeliveryTypeSettingComponent} from './components/delivery-type-setting/delivery-type-setting.component';
import {DemographicTargetingComponent} from './components/demographic-targeting/demographic-targeting.component';
import {GeoTargetingComponent} from './components/geo-targeting/geo-targeting.component';
import {GeoTargetingLocationComponent} from './components/geo-targeting-location/geo-targeting-location.component';
import {ZipTargetingComponent} from './components/zip-targeting/zip-targeting.component';
import {OperatingSystemListComponent} from './components/operating-system-list/operating-system-list.component';
import {OperatingSystemComponent} from './components/operating-system/operating-system.component';
import {TrackingCodeSettingComponent} from './components/tracking-code-setting/tracking-code-setting.component';
import {TrackingPixelSettingComponent} from './components/tracking-pixel-setting/tracking-pixel-setting.component';
import {InterestTargetingComponent} from './components/interest-targeting/interest-targeting.component';
import {PublisherGroupTargetingComponent} from './components/publisher-groups-targeting/publisher-groups-targeting.component';
import {RetargetingComponent} from './components/retargeting/retargeting.component';
import {BiddingTypeSettingComponent} from './components/bidding-type-setting/bidding-type-setting.component';
import {AdGroupAutopilotStateSettingComponent} from './components/ad-group-autopilot-state-setting/ad-group-autopilot-state-setting.component';
import {AdGroupRTBSourcesManagementSettingComponent} from './components/ad-group-rtb-sources-management-setting/ad-group-rtb-sources-management-setting.component';
import {HacksComponent} from './components/hacks/hacks.component';
import {DealsComponent} from './components/deals/deals.component';
import {BidModifiersOverviewComponent} from './components/bid-modifiers-overview/bid-modifiers-overview.component';
import {SettingsDrawerFooterComponent} from './components/settings-drawer-footer/settings-drawer-footer.component';
import {SettingsDrawerHeaderComponent} from './components/settings-drawer-header/settings-drawer-header.component';
import {CampaignGoalsComponent} from './components/campaign-goals/campaign-goals.component';
import {CampaignGoalComponent} from './components/campaign-goal/campaign-goal.component';
import {CampaignGoalEditFormComponent} from './components/campaign-goal-edit-form/campaign-goal-edit-form.component';
import {CampaignBudgetsOverviewComponent} from './components/campaign-budgets-overview/campaign-budgets-overview.component';
import {CampaignBudgetsListComponent} from './components/campaign-budgets-list/campaign-budgets-list.component';
import {CampaignBudgetEditFormComponent} from './components/campaign-budget-edit-form/campaign-budget-edit-form.component';
import {CampaignBudgetOptimizationComponent} from './components/campaign-budget-optimization/campaign-budget-optimization.component';
import {CampaignPerformanceTrackingComponent} from './components/campaign-performance-tracking/campaign-performance-tracking.component';
import {MediaSourcesComponent} from './components/media-sources/media-sources.component';
import {DealsListComponent} from './components/deals-list/deals-list.component';
import {DealComponent} from './components/deal/deal.component';
import {RouterModule} from '@angular/router';
import {ENTITY_MANAGER_ROUTES} from './entity-manager.routes';
import {CanActivateEntitySettingsGuard} from './route-guards/canActivateEntitySettings.guard';

@NgModule({
    declarations: [
        EntitySettingsRouterOutlet,
        AccountSettingsDrawerView,
        CampaignSettingsDrawerView,
        AdGroupSettingsDrawerView,
        SettingsDrawerHeaderComponent,
        SettingsDrawerFooterComponent,
        DaypartingSettingComponent,
        DeliveryTypeSettingComponent,
        BiddingTypeSettingComponent,
        DemographicTargetingComponent,
        GeoTargetingComponent,
        GeoTargetingLocationComponent,
        ZipTargetingComponent,
        OperatingSystemListComponent,
        OperatingSystemComponent,
        TrackingCodeSettingComponent,
        TrackingPixelSettingComponent,
        InterestTargetingComponent,
        PublisherGroupTargetingComponent,
        RetargetingComponent,
        AdGroupAutopilotStateSettingComponent,
        AdGroupRTBSourcesManagementSettingComponent,
        HacksComponent,
        DealsComponent,
        BidModifiersOverviewComponent,
        CampaignGoalsComponent,
        CampaignGoalComponent,
        CampaignGoalEditFormComponent,
        CampaignBudgetsOverviewComponent,
        CampaignBudgetsListComponent,
        CampaignPerformanceTrackingComponent,
        CampaignBudgetEditFormComponent,
        CampaignBudgetOptimizationComponent,
        MediaSourcesComponent,
        DealsListComponent,
        DealComponent,
    ],
    imports: [SharedModule, RouterModule.forChild(ENTITY_MANAGER_ROUTES)],
    providers: [CanActivateEntitySettingsGuard],
    entryComponents: [EntitySettingsRouterOutlet],
})
export class EntityManagerModule {}
