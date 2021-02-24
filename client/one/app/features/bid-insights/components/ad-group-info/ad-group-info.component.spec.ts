import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {AdGroupInfoStep} from '../../bid-insights.constants';
import {AdGroupSectionInfo} from '../../types/ad-group-section-info';
import {AdGroupInfoComponent} from './ad-group-info.component';

describe('AdGroupInfoComponent', () => {
    let component: AdGroupInfoComponent;
    let fixture: ComponentFixture<AdGroupInfoComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [AdGroupInfoComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(AdGroupInfoComponent);
        component = fixture.componentInstance;
        component.step = AdGroupInfoStep.TARGETING;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly format ad group info items', () => {
        const adGroupInfo: AdGroupSectionInfo[] = [
            {
                title: 'Geolocation Targeting',
                items: [
                    'Spain',
                    'Italy',
                    'Canary Islands',
                    'Poland',
                    'Finland',
                    'Sweden',
                    'Norway',
                ],
            },
            {
                title: 'Device Targeting',
                items: ['Desktop', 'Mobile'],
            },
        ];
        component.adGroupInfo = adGroupInfo;
        component.ngOnChanges();
        expect(component.formattedAdGroupInfo).toEqual([
            {
                title: 'Geolocation Targeting',
                items:
                    'Spain, Italy, Canary Islands, Poland, Finland, Sweden, Norway',
                truncatedItems: 'Spain, Italy, Canary Islands, Poland, Finland',
                isTruncated: true,
            },
            {
                title: 'Device Targeting',
                items: 'Desktop, Mobile',
                truncatedItems: 'Desktop, Mobile',
                isTruncated: false,
            },
        ]);
    });
});
