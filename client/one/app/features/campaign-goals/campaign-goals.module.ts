import {NgModule} from '@angular/core';
import {SharedModule} from '../../shared/shared.module';
import {CampaignGoalsService} from './services/campaign-goals.service';

@NgModule({
    imports: [SharedModule],
    providers: [CampaignGoalsService],
})
export class CampaignGoalsModule {}
