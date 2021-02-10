import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {EntitySelectorComponent} from './entity-selector.component';
import {SelectListComponent} from '../select-list/select-list.component';
import {SelectInputComponent} from '../select-input/select-input.component';
import {TextHighlightDirective} from '../../directives/text-highlight/text-highlight.directive';
import {NgSelectModule} from '@ng-select/ng-select';
import {LoaderComponent} from '../loader/loader.component';

describe('EntitySelectorComponent', () => {
    let component: EntitySelectorComponent;
    let fixture: ComponentFixture<EntitySelectorComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                EntitySelectorComponent,
                SelectListComponent,
                SelectInputComponent,
                TextHighlightDirective,
                LoaderComponent,
            ],
            imports: [FormsModule, NgSelectModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(EntitySelectorComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
