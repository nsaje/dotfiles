import {ActivatedRoute, Router} from '@angular/router';
import * as commonHelper from './common.helpers';

export function getActivatedRoute(router: Router): ActivatedRoute {
    let route = router.routerState.root;
    while (commonHelper.isDefined(route.firstChild)) {
        route = route.firstChild;
    }
    return route;
}
