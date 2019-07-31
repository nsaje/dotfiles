import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {SelectSettingComponent} from '../select-setting/select-setting.component';
import {TextSettingComponent} from '../text-setting/text-setting.component';
import {CampaignPerformanceTrackingComponent} from './campaign-performance-tracking.component';

describe('CampaignPerformanceTrackingComponent', () => {
    let component: CampaignPerformanceTrackingComponent;
    let fixture: ComponentFixture<CampaignPerformanceTrackingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                CampaignPerformanceTrackingComponent,
                SelectSettingComponent,
                TextSettingComponent,
            ],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignPerformanceTrackingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
