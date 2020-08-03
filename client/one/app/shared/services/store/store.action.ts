interface Action<T> {
    payload: T;
}

export class StoreAction<T> implements Action<T> {
    payload: T;

    constructor(payload: T) {
        this.payload = payload;
    }
}
