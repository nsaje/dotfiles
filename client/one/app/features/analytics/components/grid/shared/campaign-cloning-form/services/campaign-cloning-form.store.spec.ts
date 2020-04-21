import {CampaignCloningFormStore} from './campaign-cloning-form.store';
import {CampaignService} from '../../../../../../../core/entities/services/campaign/campaign.service';
import {fakeAsync, tick} from '@angular/core/testing';
import {of} from 'rxjs';
import {CampaignCloningFormStoreState} from './campaign-cloning-form.store.state';
import {AdGroupState, AdState} from '../../../../../../../app.constants';
import {CampaignCloningRule} from '../campaign-cloning.constants';
import {extendAvailableConversionPixelsWithEditedConversionPixel} from '../../../../../../entity-manager/helpers/campaign-goals.helpers';

describe('CampaignCloningFormStore', () => {
    let serviceStub: jasmine.SpyObj<CampaignService>;
    let store: CampaignCloningFormStore;
    let mockedCampaignName: string;
    let mockedCampaignId: string;

    beforeEach(() => {
        serviceStub = jasmine.createSpyObj(CampaignService.name, ['clone']);
        store = new CampaignCloningFormStore(serviceStub);
        mockedCampaignName = 'Test campaign';
        mockedCampaignId = '123';
    });

    it('should correctly init the store', () => {
        expect(store.state).toEqual(new CampaignCloningFormStoreState());
        store.init(mockedCampaignName);
        expect(store.state.campaignCloneSettings).toEqual({
            destinationCampaignName: 'Test campaign (copy)',
            cloneAdGroups: true,
            cloneAds: true,
            adGroupStateOverride: null,
            adStateOverride: null,
        });
        expect(store.state.cloneRule).toEqual(CampaignCloningRule.ADS);
    });

    it('should correctly set destination campaign name', () => {
        const destinationCampaignName = 'Destination campaign';
        store.setDestinationCampaignName(destinationCampaignName);
        expect(
            store.state.campaignCloneSettings.destinationCampaignName
        ).toEqual(destinationCampaignName);
    });

    it('should correctly set clone rule', () => {
        const cloneRule = CampaignCloningRule.CAMPAIGN;
        store.setCloneRule(cloneRule);
        expect(store.state.campaignCloneSettings.cloneAds).toEqual(false);
        expect(store.state.campaignCloneSettings.cloneAdGroups).toEqual(false);
        expect(store.state.cloneRule).toEqual(cloneRule);
    });

    it('should correctly set setAdGroupStateOverride value', () => {
        const adGroupStateOverride = AdGroupState.ACTIVE;
        store.setAdGroupStateOverride(adGroupStateOverride);
        expect(store.state.campaignCloneSettings.adGroupStateOverride).toEqual(
            adGroupStateOverride
        );
    });

    it('should correctly set setAdStateOverride value', () => {
        const adStateOverride = AdState.ACTIVE;
        store.setAdStateOverride(adStateOverride);
        expect(store.state.campaignCloneSettings.adStateOverride).toEqual(
            adStateOverride
        );
    });

    it('should correctly clone campaign', fakeAsync(() => {
        serviceStub.clone.and.returnValue(of()).calls.reset();

        store.init(mockedCampaignName);
        store.clone(mockedCampaignId);
        tick();

        expect(serviceStub.clone).toHaveBeenCalledTimes(1);
        expect(serviceStub.clone).toHaveBeenCalledWith(
            mockedCampaignId,
            store.state.campaignCloneSettings,
            jasmine.any(Function)
        );
    }));
});
