import {TestBed, ComponentFixture} from '@angular/core/testing';
import {PortalComponent} from './portal.component';
import {PortalModule} from '@angular/cdk/portal';

describe('PortalComponent', () => {
    let component: PortalComponent;
    let fixture: ComponentFixture<PortalComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [PortalComponent],
            imports: [PortalModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(PortalComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
