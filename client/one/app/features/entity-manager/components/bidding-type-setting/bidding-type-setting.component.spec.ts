import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {BiddingTypeSettingComponent} from './bidding-type-setting.component';

describe('BiddingTypeSettingComponent', () => {
    let component: BiddingTypeSettingComponent;
    let fixture: ComponentFixture<BiddingTypeSettingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [BiddingTypeSettingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BiddingTypeSettingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
