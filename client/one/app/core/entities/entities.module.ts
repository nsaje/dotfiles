import {NgModule} from '@angular/core';
import {AdGroupEndpoint} from './services/ad-group/ad-group.endpoint';
import {AdGroupService} from './services/ad-group/ad-group.service';
import {EntitiesUpdatesService} from './services/entities-updates.service';
import {BidModifierUpdatesService} from '../bid-modifiers/services/bid-modifier-updates.service';
import {CampaignEndpoint} from './services/campaign/campaign.endpoint';
import {CampaignService} from './services/campaign/campaign.service';
import {AccountEndpoint} from './services/account/account.endpoint';
import {AccountService} from './services/account/account.service';
import {AgencyEndpoint} from './services/agency/agency.endpoint';
import {AgencyService} from './services/agency/agency.service';

@NgModule({
    providers: [
        AdGroupService,
        AdGroupEndpoint,
        CampaignEndpoint,
        CampaignService,
        AccountEndpoint,
        AccountService,
        EntitiesUpdatesService,
        BidModifierUpdatesService,
        AgencyEndpoint,
        AgencyService,
    ],
})
export class EntitiesModule {}
