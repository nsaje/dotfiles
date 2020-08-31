import {IncludeExcludeType} from '../../../app.constants';
import {Browser} from '../../../core/entities/types/common/browser';

export interface BrowserTargeting {
    browser: Browser;
    includeExcludeType: IncludeExcludeType;
}
