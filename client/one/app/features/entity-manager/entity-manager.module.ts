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
