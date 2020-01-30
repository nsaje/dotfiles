import {ResizeObserver, ResizeObserverEntry} from '@juggle/resize-observer';
import {ResizeObserverCallback} from '@juggle/resize-observer/lib/ResizeObserverCallback';

// TODO (msuber): remove this helper/wrapper when
// https://github.com/WICG/ResizeObserver/issues/38
// is resolved and merged to master.
export class ResizeObserverHelper extends ResizeObserver {
    private firstObserve: boolean = true;

    constructor(callback: ResizeObserverCallback) {
        super((entries: ResizeObserverEntry[], observer: ResizeObserver) => {
            if (this.firstObserve) {
                this.firstObserve = false;
                return;
            }
            callback(entries, observer);
        });
    }

    unobserve(target: Element): void {
        this.firstObserve = true;
        super.unobserve(target);
    }

    disconnect(): void {
        this.firstObserve = true;
        super.disconnect();
    }
}
