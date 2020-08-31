import './browser-targeting.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnChanges,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {Browser} from '../../../../core/entities/types/common/browser';
import {IncludeExcludeType} from '../../../../app.constants';
import * as arrayHelpers from '../../../../shared/helpers/array.helpers';
import {BrowserTargeting} from '../../types/browser-targeting';
import {AVAILABLE_BROWSERS, BROWSER_NAMES} from './browser-targeting.config';
import {INCLUDE_EXCLUDE_TYPES} from '../../entity-manager.config';
import {FormattedBrowser} from '../../types/formatted-browser';

@Component({
    selector: 'zem-browser-targeting',
    templateUrl: './browser-targeting.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class BrowserTargetingComponent implements OnChanges {
    @Input()
    includedBrowsers: Browser[];
    @Input()
    excludedBrowsers: Browser[];
    @Input()
    isDisabled: boolean;
    @Output()
    addBrowserTargeting: EventEmitter<BrowserTargeting> = new EventEmitter<
        BrowserTargeting
    >();
    @Output()
    removeBrowserTargeting: EventEmitter<BrowserTargeting> = new EventEmitter<
        BrowserTargeting
    >();
    @Output()
    includeExcludeChange: EventEmitter<IncludeExcludeType> = new EventEmitter<
        IncludeExcludeType
    >();

    availableBrowsers: FormattedBrowser[] = AVAILABLE_BROWSERS;
    formattedSelectedBrowsers: FormattedBrowser[] = [];

    includeExcludeType: IncludeExcludeType = IncludeExcludeType.INCLUDE;
    includeExcludeTypes = INCLUDE_EXCLUDE_TYPES;
    includeExcludeEnum = IncludeExcludeType;

    ngOnChanges() {
        if (!arrayHelpers.isEmpty(this.excludedBrowsers)) {
            this.formattedSelectedBrowsers = this.getFormattedSelectedBrowsers(
                this.excludedBrowsers
            );
            this.includeExcludeType = IncludeExcludeType.EXCLUDE;
        } else {
            this.formattedSelectedBrowsers = this.getFormattedSelectedBrowsers(
                this.includedBrowsers
            );
            this.includeExcludeType = IncludeExcludeType.INCLUDE;
        }
    }

    onAddBrowserTargeting(browser: FormattedBrowser) {
        this.addBrowserTargeting.emit({
            browser: {family: browser.family},
            includeExcludeType: this.includeExcludeType,
        });
    }

    onRemoveBrowserTargeting(browser: FormattedBrowser) {
        this.removeBrowserTargeting.emit({
            browser: {family: browser.family},
            includeExcludeType: this.includeExcludeType,
        });
    }

    private getFormattedSelectedBrowsers(browsers: Browser[]) {
        return browsers.map(browser => {
            return {
                family: browser.family,
                name: BROWSER_NAMES[browser.family],
            };
        });
    }
}
