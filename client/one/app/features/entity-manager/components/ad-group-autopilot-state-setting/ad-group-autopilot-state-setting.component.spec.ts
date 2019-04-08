import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {AdGroupAutopilotStateSettingComponent} from './ad-group-autopilot-state-setting.component';
import {CampaignGoalKPI} from '../../../../app.constants';
import {AD_GROUP_AUTOPILOT_STATE_SETTING_CONFIG} from './ad-group-autopilot-state-setting.config';

describe('AdGroupAutopilotStateSettingComponent', () => {
    let component: AdGroupAutopilotStateSettingComponent;
    let fixture: ComponentFixture<AdGroupAutopilotStateSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [AdGroupAutopilotStateSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(
            AdGroupAutopilotStateSettingComponent
        );
        component = fixture.componentInstance;
    });

    it('should set optimization objective text correctly on inputs changes', () => {
        component.optimizationObjective = CampaignGoalKPI.CPA;
        component.ngOnChanges();
        expect(component.optimizationObjectiveText).toBe(
            AD_GROUP_AUTOPILOT_STATE_SETTING_CONFIG.optimizationObjectivesTexts[
                CampaignGoalKPI.CPA
            ]
        );
    });

    it('should set optimization objective text to default text on inputs changes when optimization objective is unknown', () => {
        component.ngOnChanges();
        expect(component.optimizationObjectiveText).toBe(
            AD_GROUP_AUTOPILOT_STATE_SETTING_CONFIG.optimizationObjectivesTexts
                .default
        );
    });

    it('should set cpa optimization note correctly on inputs changes for non CPA objectives', () => {
        component.optimizationObjective = CampaignGoalKPI.CPC;
        component.ngOnChanges();
        expect(component.cpaOptimizationNote).toBe(null);
    });

    it('should set cpa optimization note correctly on inputs changes for CPA objective', () => {
        component.optimizationObjective = CampaignGoalKPI.CPA;
        component.ngOnChanges();
        expect(component.cpaOptimizationNote).toBeDefined();
    });
});
