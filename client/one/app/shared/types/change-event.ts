export interface ChangeEvent<T> {
    target: T;
    changes: Partial<T>;
}
