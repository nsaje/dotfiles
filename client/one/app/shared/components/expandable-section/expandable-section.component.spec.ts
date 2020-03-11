import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ExpandableSectionComponent} from './expandable-section.component';

describe('ExpandableSectionComponent', () => {
    let component: ExpandableSectionComponent;
    let fixture: ComponentFixture<ExpandableSectionComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ExpandableSectionComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ExpandableSectionComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
