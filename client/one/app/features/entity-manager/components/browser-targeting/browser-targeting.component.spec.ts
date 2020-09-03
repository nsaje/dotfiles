import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {BrowserTargetingComponent} from './browser-targeting.component';
import {IncludeExcludeType, BrowserFamily} from '../../../../app.constants';
import {BROWSER_NAMES} from './browser-targeting.config';

describe('BrowserTargetingComponent', () => {
    let component: BrowserTargetingComponent;
    let fixture: ComponentFixture<BrowserTargetingComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [BrowserTargetingComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BrowserTargetingComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly set include exclude type', () => {
        component.includedBrowsers = [{family: BrowserFamily.CHROME}];
        component.excludedBrowsers = [];
        component.ngOnChanges();
        expect(component.includeExcludeType).toEqual(
            IncludeExcludeType.INCLUDE
        );

        component.includedBrowsers = [];
        component.excludedBrowsers = [{family: BrowserFamily.CHROME}];
        component.ngOnChanges();
        expect(component.includeExcludeType).toEqual(
            IncludeExcludeType.EXCLUDE
        );
    });

    it('should correctly format browsers', () => {
        component.includedBrowsers = [{family: BrowserFamily.CHROME}];
        component.excludedBrowsers = [];
        component.ngOnChanges();

        expect(component.formattedSelectedBrowsers).toEqual([
            {
                family: BrowserFamily.CHROME,
                name: BROWSER_NAMES[BrowserFamily.CHROME],
            },
        ]);
    });
});
