import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {MediaSourcesComponent} from './media-sources.component';

describe('MediaSourcesComponent', () => {
    let component: MediaSourcesComponent;
    let fixture: ComponentFixture<MediaSourcesComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [MediaSourcesComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(MediaSourcesComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
