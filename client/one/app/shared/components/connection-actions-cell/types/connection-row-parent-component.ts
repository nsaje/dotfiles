export abstract class ConnectionRowParentComponent<T> {
    abstract onRemoveConnection(connection: T): any;
}
