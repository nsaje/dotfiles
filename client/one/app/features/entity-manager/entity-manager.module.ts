import {NgModule} from '@angular/core';

import {SharedModule} from '../../shared/shared.module';
import {CampaignCreatorComponent} from './components/campaign-creator/campaign-creator.component';
import {CampaignCreatorModalComponent} from './components/campaign-creator-modal/campaign-creator-modal.component';
import {CampaignTypeSelectorComponent} from './components/campaign-type-selector/campaign-type-selector.component';
import {DaypartingSettingComponent} from './components/dayparting-setting/dayparting-setting.component';

@NgModule({
    declarations: [
        CampaignCreatorComponent,
        CampaignCreatorModalComponent,
        CampaignTypeSelectorComponent,
        DaypartingSettingComponent,
    ],
    imports: [SharedModule],
    entryComponents: [
        CampaignCreatorModalComponent,
        CampaignTypeSelectorComponent,
        DaypartingSettingComponent,
    ],
})
export class EntityManagerModule {}
