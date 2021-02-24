import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {AdGroupIssueComponent} from './ad-group-issue.component';

describe('AdGroupIssueComponent', () => {
    let component: AdGroupIssueComponent;
    let fixture: ComponentFixture<AdGroupIssueComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [AdGroupIssueComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(AdGroupIssueComponent);
        component = fixture.componentInstance;
        component.issueText = '';
        component.eligibleRate = 70;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
