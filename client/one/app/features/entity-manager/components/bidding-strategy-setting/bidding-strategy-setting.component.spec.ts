import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {BiddingStrategySettingComponent} from './bidding-strategy-setting.component';

describe('BiddingStrategySettingComponent', () => {
    let component: BiddingStrategySettingComponent;
    let fixture: ComponentFixture<BiddingStrategySettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [BiddingStrategySettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BiddingStrategySettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
