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
import {DemographicTargetingComponent} from './components/demographic-targeting/demographic-targeting.component';
import {GeoTargetingComponent} from './components/geo-targeting/geo-targeting.component';
import {DeviceTargetingSettingsComponent} from './components/device-targeting-settings/device-targeting-settings.component';
import {TrackingCodeSettingComponent} from './components/tracking-code-setting/tracking-code-setting.component';
import {TrackingPixelSettingComponent} from './components/tracking-pixel-setting/tracking-pixel-setting.component';

@NgModule({
    declarations: [
        EntitySettingsRouterOutlet,
        AccountSettingsDrawerView,
        CampaignSettingsDrawerView,
        AdGroupSettingsDrawerView,
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
        DemographicTargetingComponent,
        GeoTargetingComponent,
        DeviceTargetingSettingsComponent,
        TrackingCodeSettingComponent,
        TrackingPixelSettingComponent,
    ],
    imports: [SharedModule],
    entryComponents: [
        EntitySettingsRouterOutlet,
        CampaignCreatorModalComponent,
        CampaignTypeSelectorComponent,
        DaypartingSettingComponent,
    ],
})
export class EntityManagerModule {}
