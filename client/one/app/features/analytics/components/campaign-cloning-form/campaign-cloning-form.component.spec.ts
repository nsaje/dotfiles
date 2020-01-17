import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignCloningFormComponent} from './campaign-cloning-form.component';
import {CampaignCloningFormStore} from './services/campaign-cloning-form.store';
import {CampaignService} from '../../../../core/entities/services/campaign/campaign.service';
import {CampaignEndpoint} from '../../../../core/entities/services/campaign/campaign.endpoint';
import {EntitiesUpdatesService} from '../../../../core/entities/services/entities-updates.service';

describe('CampaignCloningFormComponent', () => {
    let component: CampaignCloningFormComponent;
    let fixture: ComponentFixture<CampaignCloningFormComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CampaignCloningFormComponent],
            imports: [FormsModule, SharedModule],
            providers: [
                CampaignCloningFormStore,
                CampaignService,
                EntitiesUpdatesService,
                CampaignEndpoint,
            ],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignCloningFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
