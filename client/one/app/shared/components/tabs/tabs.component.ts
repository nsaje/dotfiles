import './tabs.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    ContentChildren,
    Input,
    QueryList,
} from '@angular/core';
import {TabDirective} from './tab.directive';

@Component({
    selector: 'zem-tabs',
    templateUrl: './tabs.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TabsComponent {
    @ContentChildren(TabDirective)
    tabs: QueryList<TabDirective>;

    @Input()
    animated: boolean = false;

    currentTabIndex: number = 0;
}
